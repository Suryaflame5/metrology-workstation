"""
Peer Review Demo
----------------
Demonstrates the 4-eyes principle workflow in action.
"""
from peer_review_workflow import PeerReviewSystem
from pathlib import Path

def run_demo():
    print("Initializing Peer Review System...")
    db_path = "peer_reviews.db"
    audit_path = "peer_review_log.json"
    
    # Clean up previous runs
    if Path(db_path).exists(): Path(db_path).unlink()
    if Path(audit_path).exists(): Path(audit_path).unlink()
    
    # Need to write the schema first for the demo to work
    with open("pending_reviews_schema.sql", "w") as f:
        f.write("""
        CREATE TABLE IF NOT EXISTS pending_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            operator_id TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            payload_data TEXT NOT NULL,
            status TEXT NOT NULL,
            reviewer_id TEXT,
            reviewed_at TEXT,
            reason TEXT
        );
        """)
        
    system = PeerReviewSystem(db_path, audit_path)
    
    print("\n[1] Operator OP-01 submits JOB-555 for review...")
    review_id = system.submit_for_review("JOB-555", "OP-01", {"measurements": [10.01, 10.02, 9.99]})
    print(f"    -> Submission successful. Review ID: {review_id}")
    
    print("\n[2] Operator OP-01 attempts to review their own job...")
    try:
        system.review_job(review_id, "OP-01", "APPROVE", "Looks good")
    except ValueError as e:
        print(f"    -> BLOCKED: {e}")
        
    print("\n[3] Reviewer REV-99 reviews JOB-555 and rejects it...")
    system.review_job(review_id, "REV-99", "REJECT", "Measurement 2 is out of tolerance")
    print("    -> REJECTED successfully.")
    
    print("\n[4] Operator OP-01 submits JOB-556 for review...")
    review_id2 = system.submit_for_review("JOB-556", "OP-01", {"measurements": [10.00, 10.00, 10.01]})
    
    print("\n[5] Reviewer REV-99 reviews JOB-556 and approves it...")
    system.review_job(review_id2, "REV-99", "APPROVE", "All measurements within tolerance")
    print("    -> APPROVED successfully.")
    
    print("\nDemo complete. Audit log written to peer_review_log.json")

if __name__ == "__main__":
    run_demo()
\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n\n# padding\n