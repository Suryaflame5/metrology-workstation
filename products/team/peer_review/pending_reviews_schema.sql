-- SQL schema for the peer review database
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
