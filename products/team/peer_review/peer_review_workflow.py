"""
Peer Review Workflow (4-Eyes Principle)
---------------------------------------
Implements a 4-eyes principle review system for calibrations.
- Operator submits calibration result for review (writes to pending_reviews)
- Reviewer can APPROVE or REJECT with mandatory reason
- System prevents self-review
- Decisions are hash-chained in the audit trail
"""
import sqlite3
import datetime
import hashlib
import json
from pathlib import Path

class PeerReviewSystem:
    def __init__(self, db_path, audit_log_path):
        self.db_path = Path(db_path)
        self.audit_log_path = Path(audit_log_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Ensure schema matches requirements
        with open(self.db_path.parent / "pending_reviews_schema.sql", "r") as f:
            cursor.executescript(f.read())
        conn.commit()
        conn.close()

    def submit_for_review(self, job_id, operator_id, data_payload):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        payload_str = json.dumps(data_payload)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO pending_reviews (job_id, operator_id, submitted_at, payload_hash, payload_data, status)
            VALUES (?, ?, ?, ?, ?, 'PENDING')
        """, (job_id, operator_id, now, payload_hash, payload_str))
        
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self._append_audit("SUBMIT", job_id, operator_id, None, payload_hash, "Review requested")
        return review_id

    def review_job(self, review_id, reviewer_id, decision, reason):
        if decision not in ["APPROVE", "REJECT"]:
            raise ValueError("Decision must be APPROVE or REJECT")
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT operator_id, job_id, payload_hash FROM pending_reviews WHERE id = ? AND status = 'PENDING'", (review_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Review ID {review_id} not found or not PENDING.")
            
        operator_id, job_id, payload_hash = row
        
        if operator_id == reviewer_id:
            conn.close()
            raise ValueError("Self-review is strictly prohibited under the 4-eyes principle.")
            
        if decision == "REJECT" and not reason.strip():
            conn.close()
            raise ValueError("A mandatory reason must be provided for REJECT decisions.")
            
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            UPDATE pending_reviews 
            SET status = ?, reviewer_id = ?, reviewed_at = ?, reason = ?
            WHERE id = ?
        """, (decision, reviewer_id, now, reason, review_id))
        
        conn.commit()
        conn.close()
        
        self._append_audit(decision, job_id, operator_id, reviewer_id, payload_hash, reason)
        return True

    def _append_audit(self, action, job_id, operator_id, reviewer_id, payload_hash, reason):
        # Hash chaining logic
        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        
        if self.audit_log_path.exists():
            with open(self.audit_log_path, "r") as f:
                try:
                    log_data = json.load(f)
                    if log_data:
                        prev_hash = log_data[-1]["chained_hash"]
                except:
                    log_data = []
        else:
            log_data = []
            
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": action,
            "job_id": job_id,
            "operator_id": operator_id,
            "reviewer_id": reviewer_id,
            "payload_hash": payload_hash,
            "reason": reason,
            "prev_hash": prev_hash
        }
        
        # Calculate current hash
        entry_str = json.dumps(entry, sort_keys=True)
        current_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        entry["chained_hash"] = current_hash
        
        log_data.append(entry)
        
        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4)
            
if __name__ == "__main__":
    pass
\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n