"""
Background Job Architecture

Production-grade job processing system with:
- Job queue management
- Worker processes
- Job scheduling and monitoring
- Error handling and retry logic
- Job history and audit trails
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import secrets
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor

from ..infrastructure.security.rbac import Role


logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Job:
    """Background job definition."""
    job_id: str
    job_type: str
    task_function: Callable
    task_args: tuple = field(default_factory=tuple)
    task_kwargs: dict = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: Optional[int] = None
    created_by_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobResult:
    """Result of job execution."""
    job_id: str
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0


class JobQueue:
    """Priority-based job queue."""
    
    def __init__(self):
        """Initialize job queue."""
        self._queue = queue.PriorityQueue()
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
    
    def enqueue(self, job: Job):
        """
        Add job to queue.
        
        Args:
            job: Job to enqueue
        """
        with self._lock:
            self._jobs[job.job_id] = job
            # Use negative priority for higher priority to be processed first
            priority = -job.priority.value
            self._queue.put((priority, job.job_id))
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[Job]:
        """
        Get next job from queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Next job or None if queue is empty
        """
        try:
            priority, job_id = self._queue.get(timeout=timeout)
            with self._lock:
                return self._jobs.get(job_id)
        except queue.Empty:
            return None
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job or None if not found
        """
        with self._lock:
            return self._jobs.get(job_id)
    
    def remove_job(self, job_id: str):
        """
        Remove job from queue.
        
        Args:
            job_id: Job ID to remove
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]


class BackgroundJobProcessor:
    """
    Production-grade background job processor.
    
    Handles job scheduling, execution, monitoring, and retry logic
    with thread-based worker pool.
    """
    
    def __init__(self, num_workers: int = 4):
        """
        Initialize background job processor.
        
        Args:
            num_workers: Number of worker threads
        """
        self.job_queue = JobQueue()
        self.job_results: Dict[str, JobResult] = {}
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.is_running = False
        self._workers: List[threading.Thread] = []
        self._lock = threading.Lock()
        
        logger.info(f"Background job processor initialized with {num_workers} workers")
    
    def start(self):
        """Start the job processor."""
        with self._lock:
            if self.is_running:
                return
            
            self.is_running = True
            
            # Start worker threads
            for i in range(self.executor._max_workers):
                worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"JobWorker-{i}")
                worker.start()
                self._workers.append(worker)
            
            logger.info("Background job processor started")
    
    def stop(self):
        """Stop the job processor."""
        with self._lock:
            if not self.is_running:
                return
            
            self.is_running = False
            
            # Wait for workers to finish
            for worker in self._workers:
                worker.join(timeout=5.0)
            
            self._workers.clear()
            
            logger.info("Background job processor stopped")
    
    def submit_job(self, job: Job) -> str:
        """
        Submit a job for processing.
        
        Args:
            job: Job to submit
            
        Returns:
            Job ID
        """
        self.job_queue.enqueue(job)
        
        # Initialize job result
        self.job_results[job.job_id] = JobResult(
            job_id=job.job_id,
            status=JobStatus.PENDING
        )
        
        logger.info(f"Job {job.job_id} submitted for processing")
        return job.job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        job = self.job_queue.get_job(job_id)
        if not job:
            return False
        
        # Remove from queue
        self.job_queue.remove_job(job_id)
        
        # Update result
        if job_id in self.job_results:
            self.job_results[job_id].status = JobStatus.CANCELLED
            self.job_results[job_id].completed_at = datetime.now()
        
        logger.info(f"Job {job_id} cancelled")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """
        Get job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job result or None if not found
        """
        return self.job_results.get(job_id)
    
    def _worker_loop(self):
        """Worker thread main loop."""
        while self.is_running:
            try:
                # Get next job
                job = self.job_queue.dequeue(timeout=1.0)
                if not job:
                    continue
                
                # Execute job
                self._execute_job(job)
                
            except Exception as e:
                logger.error(f"Worker thread error: {e}")
    
    def _execute_job(self, job: Job):
        """
        Execute a job with retry logic.
        
        Args:
            job: Job to execute
        """
        job_result = self.job_results.get(job.job_id)
        if not job_result:
            job_result = JobResult(job_id=job.job_id, status=JobStatus.PENDING)
            self.job_results[job.job_id] = job_result
        
        retry_count = 0
        max_retries = job.max_retries
        
        while retry_count <= max_retries:
            # Update status
            job_result.status = JobStatus.RUNNING if retry_count == 0 else JobStatus.RETRYING
            job_result.started_at = datetime.now()
            job_result.retry_count = retry_count
            
            try:
                # Execute with timeout if specified
                if job.timeout_seconds:
                    result = self.executor.submit(
                        job.task_function, *job.task_args, **job.task_kwargs
                    ).result(timeout=job.timeout_seconds)
                else:
                    result = job.task_function(*job.task_args, **job.task_kwargs)
                
                # Job completed successfully
                job_result.status = JobStatus.COMPLETED
                job_result.result = result
                job_result.completed_at = datetime.now()
                job_result.execution_time_seconds = (
                    job_result.completed_at - job_result.started_at
                ).total_seconds()
                
                logger.info(f"Job {job.job_id} completed successfully")
                return
                
            except Exception as e:
                job_result.error = str(e)
                retry_count += 1
                
                if retry_count <= max_retries:
                    logger.warning(f"Job {job.job_id} failed, retry {retry_count}/{max_retries}: {e}")
                    time.sleep(job.retry_delay_seconds)
                else:
                    # Max retries exceeded
                    job_result.status = JobStatus.FAILED
                    job_result.completed_at = datetime.now()
                    job_result.execution_time_seconds = (
                        job_result.completed_at - job_result.started_at
                    ).total_seconds()
                    
                    logger.error(f"Job {job.job_id} failed after {max_retries} retries: {e}")
                    return


class JobScheduler:
    """
    Job scheduler for recurring and delayed jobs.
    
    Handles scheduled job execution with cron-like functionality.
    """
    
    def __init__(self, job_processor: BackgroundJobProcessor):
        """
        Initialize job scheduler.
        
        Args:
            job_processor: Background job processor
        """
        self.job_processor = job_processor
        self.scheduled_jobs: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info("Job scheduler initialized")
    
    def start(self):
        """Start the job scheduler."""
        with self._lock:
            if self.is_running:
                return
            
            self.is_running = True
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._scheduler_thread.start()
            
            logger.info("Job scheduler started")
    
    def stop(self):
        """Stop the job scheduler."""
        with self._lock:
            if not self.is_running:
                return
            
            self.is_running = False
            
            if self._scheduler_thread:
                self._scheduler_thread.join(timeout=5.0)
            
            logger.info("Job scheduler stopped")
    
    def schedule_job(self, job: Job, run_at: datetime) -> str:
        """
        Schedule a job to run at a specific time.
        
        Args:
            job: Job to schedule
            run_at: When to run the job
            
        Returns:
            Schedule ID
        """
        schedule_id = secrets.token_hex(16)
        
        with self._lock:
            self.scheduled_jobs[schedule_id] = {
                "job": job,
                "run_at": run_at,
                "recurring": False
            }
        
        logger.info(f"Job {job.job_id} scheduled for {run_at}")
        return schedule_id
    
    def schedule_recurring_job(self, job: Job, interval_seconds: int,
                             start_at: Optional[datetime] = None) -> str:
        """
        Schedule a recurring job.
        
        Args:
            job: Job to schedule
            interval_seconds: Interval between runs in seconds
            start_at: When to start (defaults to now)
            
        Returns:
            Schedule ID
        """
        schedule_id = secrets.token_hex(16)
        start_at = start_at or datetime.now()
        
        with self._lock:
            self.scheduled_jobs[schedule_id] = {
                "job": job,
                "run_at": start_at,
                "interval_seconds": interval_seconds,
                "recurring": True,
                "last_run": None
            }
        
        logger.info(f"Recurring job {job.job_id} scheduled with interval {interval_seconds}s")
        return schedule_id
    
    def cancel_scheduled_job(self, schedule_id: str) -> bool:
        """
        Cancel a scheduled job.
        
        Args:
            schedule_id: Schedule ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        with self._lock:
            if schedule_id in self.scheduled_jobs:
                del self.scheduled_jobs[schedule_id]
                logger.info(f"Scheduled job {schedule_id} cancelled")
                return True
            return False
    
    def _scheduler_loop(self):
        """Scheduler main loop."""
        while self.is_running:
            try:
                now = datetime.now()
                jobs_to_run = []
                
                with self._lock:
                    for schedule_id, schedule_info in list(self.scheduled_jobs.items()):
                        if schedule_info["run_at"] <= now:
                            jobs_to_run.append((schedule_id, schedule_info))
                
                # Process jobs to run
                for schedule_id, schedule_info in jobs_to_run:
                    job = schedule_info["job"]
                    
                    # Submit job to processor
                    self.job_processor.submit_job(job)
                    
                    with self._lock:
                        if schedule_info["recurring"]:
                            # Schedule next run
                            schedule_info["run_at"] = now + timedelta(
                                seconds=schedule_info["interval_seconds"]
                            )
                            schedule_info["last_run"] = now
                        else:
                            # Remove non-recurring job
                            del self.scheduled_jobs[schedule_id]
                
                # Sleep for 1 second
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")


# Global job processor instance
_job_processor: Optional[BackgroundJobProcessor] = None
_job_scheduler: Optional[JobScheduler] = None


def get_job_processor() -> BackgroundJobProcessor:
    """Get or create the global job processor instance."""
    global _job_processor
    if _job_processor is None:
        _job_processor = BackgroundJobProcessor(num_workers=4)
        _job_processor.start()
    return _job_processor


def get_job_scheduler() -> JobScheduler:
    """Get or create the global job scheduler instance."""
    global _job_scheduler
    if _job_scheduler is None:
        _job_scheduler = JobScheduler(get_job_processor())
        _job_scheduler.start()
    return _job_scheduler


def cleanup_job_system():
    """Cleanup job system resources."""
    global _job_processor, _job_scheduler
    
    if _job_scheduler:
        _job_scheduler.stop()
        _job_scheduler = None
    
    if _job_processor:
        _job_processor.stop()
        _job_processor = None
    
    logger.info("Job system cleaned up")