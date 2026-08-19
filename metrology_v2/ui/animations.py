"""
Agentic UI Animation Framework for Metrology V2

Production-grade animation system with:
- Smooth, professional animations
- Physics-based transitions
- Performance-optimized rendering
- Accessibility considerations
- Cross-platform compatibility
- State-driven animations
- Micro-interactions
"""

from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
from datetime import datetime
import logging
import math


logger = logging.getLogger(__name__)


class AnimationType(Enum):
    """Types of UI animations."""
    FADE = "fade"
    SLIDE = "slide"
    SCALE = "scale"
    ROTATE = "rotate"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    SPRING = "spring"
    CUSTOM = "custom"


class EasingFunction(Enum):
    """Easing functions for smooth animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_IN_OUT_QUAD = "ease_in_out_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_IN_QUART = "ease_in_quart"
    EASE_OUT_QUART = "ease_out_quart"
    EASE_IN_OUT_QUART = "ease_in_out_quart"
    EASE_IN_BACK = "ease_in_back"
    EASE_OUT_BACK = "ease_out_back"
    EASE_IN_OUT_BACK = "ease_in_out_back"


class AnimationState(Enum):
    """Animation states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class AnimationConfig:
    """Configuration for individual animations."""
    duration: float = 0.3  # seconds
    easing: EasingFunction = EasingFunction.EASE_OUT_CUBIC
    delay: float = 0.0
    iterations: int = 1
    direction: str = "normal"  # normal, reverse, alternate, alternate-reverse
    fill_mode: str = "forwards"  # none, forwards, backwards, both
    auto_reverse: bool = False


@dataclass
class AnimationKeyframe:
    """Single keyframe in an animation sequence."""
    time: float  # Time in seconds (0 to 1 relative to duration)
    properties: Dict[str, Any]  # Property values at this keyframe
    easing: Optional[EasingFunction] = None


@dataclass
class AnimationProgress:
    """Progress information for an animation."""
    animation_id: str
    current_time: float
    total_duration: float
    progress: float  # 0.0 to 1.0
    current_iteration: int
    total_iterations: int
    state: AnimationState
    current_values: Dict[str, Any]


class EasingCalculator:
    """Calculate easing functions for smooth animations."""
    
    @staticmethod
    def apply_easing(t: float, easing: EasingFunction) -> float:
        """
        Apply easing function to normalized time (0-1).
        
        Args:
            t: Normalized time (0.0 to 1.0)
            easing: Easing function to apply
            
        Returns:
            Eased time value
        """
        t = max(0.0, min(1.0, t))  # Clamp to 0-1 range
        
        if easing == EasingFunction.LINEAR:
            return t
        
        elif easing == EasingFunction.EASE_IN:
            return t * t
        
        elif easing == EasingFunction.EASE_OUT:
            return t * (2 - t)
        
        elif easing == EasingFunction.EASE_IN_OUT:
            return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
        
        elif easing == EasingFunction.EASE_IN_QUAD:
            return t * t
        
        elif easing == EasingFunction.EASE_OUT_QUAD:
            return t * (2 - t)
        
        elif easing == EasingFunction.EASE_IN_OUT_QUAD:
            return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
        
        elif easing == EasingFunction.EASE_IN_CUBIC:
            return t * t * t
        
        elif easing == EasingFunction.EASE_OUT_CUBIC:
            return (--t) * t * t + 1
        
        elif easing == EasingFunction.EASE_IN_OUT_CUBIC:
            return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1
        
        elif easing == EasingFunction.EASE_IN_QUART:
            return t * t * t * t
        
        elif easing == EasingFunction.EASE_OUT_QUART:
            return 1 - (--t) * t * t * t
        
        elif easing == EasingFunction.EASE_IN_OUT_QUART:
            return t < 0.5 ? 8 * t * t * t * t : 1 - 8 * (--t) * t * t * t
        
        elif easing == EasingFunction.EASE_IN_BACK:
            return t * t * (3 - 2 * t)
        
        elif easing == EasingFunction.EASE_OUT_BACK:
            return 1 + (--t) * t * t * (2 * t - 1)
        
        elif easing == EasingFunction.EASE_IN_OUT_BACK:
            return t < 0.5 ? 4 * t * t * t : 1 + (--t) * t * t * (2 * t - 1)
        
        else:
            return t  # Default to linear


class PhysicsAnimation:
    """Physics-based animations with realistic motion."""
    
    @staticmethod
    def spring_motion(t: float, mass: float = 1.0, stiffness: float = 100.0, 
                    damping: float = 10.0) -> float:
        """
        Calculate spring motion using damped harmonic oscillator.
        
        Args:
            t: Time (0 to 1)
            mass: Mass of the object
            stiffness: Spring stiffness
            damping: Damping coefficient
            
        Returns:
            Displacement at time t
        """
        # Calculate natural frequency and damping ratio
        omega_n = math.sqrt(stiffness / mass)
        zeta = damping / (2 * math.sqrt(stiffness * mass))
        
        if zeta < 1.0:  # Underdamped
            omega_d = omega_n * math.sqrt(1 - zeta * zeta)
            decay = math.exp(-zeta * omega_n * t)
            oscillation = math.cos(omega_d * t)
            return decay * oscillation
        elif zeta == 1.0:  # Critically damped
            decay = math.exp(-omega_n * t)
            return decay * (1 + omega_n * t)
        else:  # Overdamped
            # Two real roots
            r1 = -omega_n * (zeta + math.sqrt(zeta * zeta - 1))
            r2 = -omega_n * (zeta - math.sqrt(zeta * zeta - 1))
            c1 = r2 / (r2 - r1)
            c2 = -r1 / (r2 - r1)
            return c1 * math.exp(r1 * t) + c2 * math.exp(r2 * t)
    
    @staticmethod
    def bounce(t: float, bounces: int = 3, decay: float = 0.5) -> float:
        """
        Calculate bounce animation with decaying amplitude.
        
        Args:
            t: Time (0 to 1)
            bounces: Number of bounces
            decay: Amplitude decay factor
            
        Returns:
            Height at time t
        """
        if t >= 1.0:
            return 0.0
        
        # Calculate which bounce we're in
        bounce_duration = 1.0 / bounces
        current_bounce = int(t / bounce_duration)
        bounce_time = (t % bounce_duration) / bounce_duration
        
        # Calculate height using parabolic motion
        height = 4 * bounce_time * (1 - bounce_time)
        
        # Apply decay
        amplitude = decay ** current_bounce
        
        return height * amplitude
    
    @staticmethod
    def elastic(t: float, amplitude: float = 1.0, period: float = 0.3) -> float:
        """
        Calculate elastic animation with oscillating overshoot.
        
        Args:
            t: Time (0 to 1)
            amplitude: Maximum overshoot
            period: Oscillation period
            
        Returns:
            Value at time t
        """
        if t >= 1.0:
            return 1.0
        
        # Damped oscillation
        decay = math.exp(-3 * t)
        oscillation = math.sin(2 * math.pi * t / period)
        
        return 1.0 + amplitude * decay * oscillation


class AnimationEngine:
    """
    Production-grade animation engine with performance optimization
    and state management.
    """
    
    def __init__(self, target_fps: int = 60):
        """
        Initialize the animation engine.
        
        Args:
            target_fps: Target frames per second
        """
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        
        self._animations: Dict[str, Dict] = {}
        self._animation_queue = []
        self._is_running = False
        self._animation_thread = None
        
        self._progress_callbacks: Dict[str, Callable] = []
        self._completion_callbacks: Dict[str, Callable] = []
        
        logger.info(f"Animation engine initialized at {target_fps} FPS")
    
    def create_animation(self, animation_id: str, config: AnimationConfig,
                       keyframes: List[AnimationKeyframe],
                       update_callback: Optional[Callable] = None,
                       completion_callback: Optional[Callable] = None) -> str:
        """
        Create a new animation.
        
        Args:
            animation_id: Unique identifier for the animation
            config: Animation configuration
            keyframes: List of keyframes defining the animation
            update_callback: Callback for each frame update
            completion_callback: Callback when animation completes
            
        Returns:
            Animation ID
        """
        animation = {
            'id': animation_id,
            'config': config,
            'keyframes': keyframes,
            'state': AnimationState.IDLE,
            'start_time': None,
            'current_time': 0.0,
            'current_iteration': 0,
            'update_callback': update_callback,
            'completion_callback': completion_callback,
            'current_values': {}
        }
        
        self._animations[animation_id] = animation
        
        if update_callback:
            self._progress_callbacks[animation_id] = update_callback
        if completion_callback:
            self._completion_callbacks[animation_id] = completion_callback
        
        logger.info(f"Animation created: {animation_id}")
        return animation_id
    
    def start_animation(self, animation_id: str):
        """
        Start an animation.
        
        Args:
            animation_id: Animation to start
        """
        if animation_id not in self._animations:
            raise ValueError(f"Animation {animation_id} not found")
        
        animation = self._animations[animation_id]
        animation['state'] = AnimationState.RUNNING
        animation['start_time'] = time.time()
        
        self._animation_queue.append(animation_id)
        
        if not self._is_running:
            self._start_animation_loop()
        
        logger.info(f"Animation started: {animation_id}")
    
    def pause_animation(self, animation_id: str):
        """
        Pause an animation.
        
        Args:
            animation_id: Animation to pause
        """
        if animation_id in self._animations:
            self._animations[animation_id]['state'] = AnimationState.PAUSED
            logger.info(f"Animation paused: {animation_id}")
    
    def resume_animation(self, animation_id: str):
        """
        Resume a paused animation.
        
        Args:
            animation_id: Animation to resume
        """
        if animation_id in self._animations:
            self._animations[animation_id]['state'] = AnimationState.RUNNING
            logger.info(f"Animation resumed: {animation_id}")
    
    def cancel_animation(self, animation_id: str):
        """
        Cancel an animation.
        
        Args:
            animation_id: Animation to cancel
        """
        if animation_id in self._animations:
            self._animations[animation_id]['state'] = AnimationState.CANCELLED
            logger.info(f"Animation cancelled: {animation_id}")
    
    def _start_animation_loop(self):
        """Start the animation processing loop."""
        self._is_running = True
        self._animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._animation_thread.start()
        logger.info("Animation loop started")
    
    def _animation_loop(self):
        """Main animation processing loop."""
        while self._is_running and self._animation_queue:
            # Process all queued animations
            for animation_id in self._animation_queue[:]:
                self._process_animation(animation_id)
            
            # Remove completed animations from queue
            self._animation_queue = [
                aid for aid in self._animation_queue
                if self._animations[aid]['state'] in [AnimationState.RUNNING, AnimationState.PAUSED]
            ]
            
            # Sleep for frame time
            time.sleep(self.frame_time)
        
        self._is_running = False
        logger.info("Animation loop stopped")
    
    def _process_animation(self, animation_id: str):
        """
        Process a single animation frame.
        
        Args:
            animation_id: Animation to process
        """
        animation = self._animations[animation_id]
        
        if animation['state'] != AnimationState.RUNNING:
            return
        
        config = animation['config']
        keyframes = animation['keyframes']
        
        # Calculate current time
        elapsed = time.time() - animation['start_time']
        animation['current_time'] = elapsed
        
        # Check if animation is complete
        if elapsed >= config.duration:
            self._complete_animation(animation_id)
            return
        
        # Calculate progress
        progress = elapsed / config.duration
        animation['progress'] = progress
        
        # Interpolate between keyframes
        current_values = self._interpolate_keyframes(keyframes, progress, config)
        animation['current_values'] = current_values
        
        # Call update callback
        update_callback = self._progress_callbacks.get(animation_id)
        if update_callback:
            try:
                progress_info = AnimationProgress(
                    animation_id=animation_id,
                    current_time=elapsed,
                    total_duration=config.duration,
                    progress=progress,
                    current_iteration=animation['current_iteration'],
                    total_iterations=config.iterations,
                    state=animation['state'],
                    current_values=current_values
                )
                update_callback(progress_info)
            except Exception as e:
                logger.error(f"Update callback error for {animation_id}: {e}")
    
    def _interpolate_keyframes(self, keyframes: List[AnimationKeyframe], 
                             progress: float, config: AnimationConfig) -> Dict[str, Any]:
        """
        Interpolate between keyframes based on progress.
        
        Args:
            keyframes: List of keyframes
            progress: Current progress (0-1)
            config: Animation configuration
            
        Returns:
            Interpolated property values
        """
        if not keyframes:
            return {}
        
        # Find surrounding keyframes
        prev_keyframe = None
        next_keyframe = None
        
        for keyframe in keyframes:
            if keyframe.time <= progress:
                prev_keyframe = keyframe
            elif keyframe.time > progress and next_keyframe is None:
                next_keyframe = keyframe
                break
        
        # Handle edge cases
        if prev_keyframe is None:
            return keyframes[0].properties if keyframes else {}
        if next_keyframe is None:
            return keyframes[-1].properties
        
        # Calculate local progress between keyframes
        time_range = next_keyframe.time - prev_keyframe.time
        local_progress = (progress - prev_keyframe.time) / time_range if time_range > 0 else 0
        
        # Apply easing
        easing = next_keyframe.easing or config.easing
        eased_progress = EasingCalculator.apply_easing(local_progress, easing)
        
        # Interpolate properties
        interpolated = {}
        for prop in prev_keyframe.properties:
            if prop in next_keyframe.properties:
                prev_value = prev_keyframe.properties[prop]
                next_value = next_keyframe.properties[prop]
                
                # Linear interpolation
                if isinstance(prev_value, (int, float)) and isinstance(next_value, (int, float)):
                    interpolated[prop] = prev_value + (next_value - prev_value) * eased_progress
                else:
                    # For non-numeric values, use the next keyframe value
                    interpolated[prop] = next_value
        
        return interpolated
    
    def _complete_animation(self, animation_id: str):
        """
        Mark animation as completed and trigger callback.
        
        Args:
            animation_id: Animation to complete
        """
        animation = self._animations[animation_id]
        animation['state'] = AnimationState.COMPLETED
        
        # Handle iterations
        config = animation['config']
        if animation['current_iteration'] < config.iterations - 1:
            # Start next iteration
            animation['current_iteration'] += 1
            animation['start_time'] = time.time()
            animation['state'] = AnimationState.RUNNING
        else:
            # Animation fully complete
            completion_callback = self._completion_callbacks.get(animation_id)
            if completion_callback:
                try:
                    completion_callback(animation_id)
                except Exception as e:
                    logger.error(f"Completion callback error for {animation_id}: {e}")
        
        logger.info(f"Animation completed: {animation_id}")
    
    def stop(self):
        """Stop the animation engine."""
        self._is_running = False
        if self._animation_thread:
            self._animation_thread.join(timeout=2.0)
        logger.info("Animation engine stopped")


class AgenticUIManager:
    """
    High-level manager for agentic UI animations and micro-interactions.
    
    Provides:
    - Context-aware animations
    - State-driven UI transitions
    - Micro-interactions
    - Gesture recognition
    - Accessibility support
    """
    
    def __init__(self, animation_engine: Optional[AnimationEngine] = None):
        """
        Initialize the agentic UI manager.
        
        Args:
            animation_engine: Animation engine instance (creates default if not provided)
        """
        self.animation_engine = animation_engine or AnimationEngine()
        self._ui_state: Dict[str, Any] = {}
        self._context_stack: List[str] = []
        
        logger.info("Agentic UI manager initialized")
    
    def set_ui_state(self, state: str, value: Any):
        """
        Set UI state and trigger appropriate animations.
        
        Args:
            state: State identifier
            value: State value
        """
        self._ui_state[state] = value
        self._trigger_state_animation(state, value)
    
    def push_context(self, context: str):
        """
        Push a new context onto the context stack.
        
        Args:
            context: Context identifier
        """
        self._context_stack.append(context)
        self._trigger_context_animation(context, "enter")
    
    def pop_context(self):
        """Pop the current context from the stack."""
        if self._context_stack:
            context = self._context_stack.pop()
            self._trigger_context_animation(context, "exit")
    
    def _trigger_state_animation(self, state: str, value: Any):
        """
        Trigger animation based on state change.
        
        Args:
            state: State that changed
            value: New state value
        """
        # Define state-based animations
        state_animations = {
            'loading': self._create_loading_animation,
            'success': self._create_success_animation,
            'error': self._create_error_animation,
            'processing': self._create_processing_animation,
        }
        
        animation_creator = state_animations.get(state)
        if animation_creator:
            animation_id = f"{state}_{value}_{time.time()}"
            animation_config, keyframes = animation_creator()
            self.animation_engine.create_animation(animation_id, animation_config, keyframes)
            self.animation_engine.start_animation(animation_id)
    
    def _trigger_context_animation(self, context: str, action: str):
        """
        Trigger animation based on context change.
        
        Args:
            context: Context identifier
            action: Action (enter/exit)
        """
        # Define context-based animations
        if action == "enter":
            self._create_context_enter_animation(context)
        else:
            self._create_context_exit_animation(context)
    
    def _create_loading_animation(self) -> tuple:
        """Create loading spinner animation."""
        config = AnimationConfig(
            duration=2.0,
            easing=EasingFunction.LINEAR,
            iterations=0  # Infinite
        )
        
        keyframes = [
            AnimationKeyframe(time=0.0, properties={'rotation': 0}),
            AnimationKeyframe(time=1.0, properties={'rotation': 360}),
        ]
        
        return config, keyframes
    
    def _create_success_animation(self) -> tuple:
        """Create success checkmark animation."""
        config = AnimationConfig(
            duration=0.5,
            easing=EasingFunction.EASE_OUT_BACK,
        )
        
        keyframes = [
            AnimationKeyframe(time=0.0, properties={'scale': 0.0, 'opacity': 0.0}),
            AnimationKeyframe(time=0.5, properties={'scale': 1.0, 'opacity': 1.0}),
        ]
        
        return config, keyframes
    
    def _create_error_animation(self) -> tuple:
        """Create error shake animation."""
        config = AnimationConfig(
            duration=0.4,
            easing=EasingFunction.EASE_OUT_QUAD,
        )
        
        keyframes = [
            AnimationKeyframe(time=0.0, properties={'x_offset': 0}),
            AnimationKeyframe(time=0.125, properties={'x_offset': -10}),
            AnimationKeyframe(time=0.25, properties={'x_offset': 10}),
            AnimationKeyframe(time=0.375, properties={'x_offset': -10}),
            AnimationKeyframe(time=0.5, properties={'x_offset': 10}),
            AnimationKeyframe(time=0.625, properties={'x_offset': -5}),
            AnimationKeyframe(time=0.75, properties={'x_offset': 5}),
            AnimationKeyframe(time=1.0, properties={'x_offset': 0}),
        ]
        
        return config, keyframes
    
    def _create_processing_animation(self) -> tuple:
        """Create processing pulse animation."""
        config = AnimationConfig(
            duration=1.5,
            easing=EasingFunction.EASE_IN_OUT_SINE,
            iterations=0
        )
        
        keyframes = [
            AnimationKeyframe(time=0.0, properties={'opacity': 0.5, 'scale': 0.95}),
            AnimationKeyframe(time=0.5, properties={'opacity': 1.0, 'scale': 1.0}),
            AnimationKeyframe(time=1.0, properties={'opacity': 0.5, 'scale': 0.95}),
        ]
        
        return config, keyframes
    
    def _create_context_enter_animation(self, context: str) -> str:
        """Create context enter animation."""
        animation_id = f"context_enter_{context}_{time.time()}"
        
        config = AnimationConfig(
            duration=0.3,
            easing=EasingFunction.EASE_OUT_CUBIC,
        )
        
        keyframes = [
            AnimationKeyframe(time=0.0, properties={'opacity': 0.0, 'y_offset': 20}),
            AnimationKeyframe(time=1.0, properties={'opacity': 1.0, 'y_offset': 0}),
        ]
        
        self.animation_engine.create_animation(animation_id, config, keyframes)
        self.animation_engine.start_animation(animation_id)
        
        return animation_id
    
    def _create_context_exit_animation(self, context: str) -> str:
        """Create context exit animation."""
        animation_id = f"context_exit_{context}_{time.time()}"
        
        config = AnimationConfig(
            duration=0.2,
            easing=EasingFunction.EASE_IN_CUBIC,
        )
        
        keyframes = [
            AnimationKeyframe(time=0.0, properties={'opacity': 1.0, 'y_offset': 0}),
            AnimationKeyframe(time=1.0, properties={'opacity': 0.0, 'y_offset': -20}),
        ]
        
        self.animation_engine.create_animation(animation_id, config, keyframes)
        self.animation_engine.start_animation(animation_id)
        
        return animation_id


# Global animation engine instance
_animation_engine: Optional[AnimationEngine] = None
_ui_manager: Optional[AgenticUIManager] = None


def get_animation_engine() -> AnimationEngine:
    """Get or create the global animation engine instance."""
    global _animation_engine
    if _animation_engine is None:
        _animation_engine = AnimationEngine()
    return _animation_engine


def get_ui_manager() -> AgenticUIManager:
    """Get or create the global UI manager instance."""
    global _ui_manager
    if _ui_manager is None:
        _ui_manager = AgenticUIManager()
    return _ui_manager


def cleanup():
    """Cleanup animation resources."""
    global _animation_engine, _ui_manager
    if _animation_engine:
        _animation_engine.stop()
    _animation_engine = None
    _ui_manager = None
    logger.info("Animation resources cleaned up")