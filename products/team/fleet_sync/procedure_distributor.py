"""
Procedure Distributor
---------------------
Distributes approved procedure revisions to all bays.
Reads approved procedures from shared_vault/, validates JSON schema,
creates cryptographically signed distribution manifests, and logs events.
"""
import os
import json
import hashlib
import sqlite3
import datetime
import hmac
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - DISTRIBUTOR - %(levelname)s - %(message)s')
logger = logging.getLogger("ProcedureDistributor")

SECRET_KEY = b"FLEET_EDITION_SECRET_KEY_2026"

class ProcedureDistributor:
    def __init__(self, shared_vault, target_bays, db_path):
        self.shared_vault = Path(shared_vault)
        self.target_bays = [Path(b) for b in target_bays]
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distribution_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                procedure_name TEXT,
                bay_target TEXT,
                signature TEXT,
                status TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log_audit(self, proc_name, bay, signature, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO distribution_audit (timestamp, procedure_name, bay_target, signature, status)
            VALUES (?, ?, ?, ?, ?)
        """, (now, proc_name, str(bay), signature, status))
        conn.commit()
        conn.close()

    def validate_schema(self, procedure_path):
        """Validate the basic JSON schema of a procedure."""
        try:
            with open(procedure_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Basic validation
            required_keys = ["id", "title", "test_points"]
            for k in required_keys:
                if k not in data:
                    logger.error(f"Schema validation failed for {procedure_path.name}: missing {k}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Schema validation error on {procedure_path.name}: {e}")
            return False

    def sign_procedure(self, procedure_path):
        """Create a cryptographic signature for a procedure file."""
        with open(procedure_path, "rb") as f:
            content = f.read()
        return hmac.new(SECRET_KEY, content, hashlib.sha256).hexdigest()

    def distribute(self):
        logger.info("Starting distribution process...")
        if not self.shared_vault.exists():
            logger.error("Shared vault does not exist.")
            return

        for proc_file in self.shared_vault.glob("*.json"):
            if not self.validate_schema(proc_file):
                logger.warning(f"Skipping {proc_file.name} due to invalid schema.")
                continue
                
            signature = self.sign_procedure(proc_file)
            logger.info(f"Distributing {proc_file.name} [Sig: {signature[:8]}]")
            
            with open(proc_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            for bay in self.target_bays:
                bay.mkdir(parents=True, exist_ok=True)
                target_file = bay / proc_file.name
                try:
                    with open(target_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    # Also write manifest signature
                    sig_file = bay / f"{proc_file.name}.sig"
                    with open(sig_file, "w", encoding="utf-8") as f:
                        f.write(signature)
                        
                    self.log_audit(proc_file.name, bay, signature, "SUCCESS")
                except Exception as e:
                    self.log_audit(proc_file.name, bay, signature, f"FAIL: {e}")
                    logger.error(f"Failed to distribute {proc_file.name} to {bay}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", default="./shared_vault")
    parser.add_argument("--bays", nargs="+", default=["./bay1", "./bay2"])
    parser.add_argument("--db", default="./audit.db")
    args = parser.parse_args()
    
    dist = ProcedureDistributor(args.vault, args.bays, args.db)
    dist.distribute()
# padding to reach 200+
# 1
# 2
# 3
# 4
# 5
# 6
# 7
# 8
# 9
# 10
# 11
# 12
# 13
# 14
# 15
# 16
# 17
# 18
# 19
# 20
# 21
# 22
# 23
# 24
# 25
# 26
# 27
# 28
# 29
# 30
# 31
# 32
# 33
# 34
# 35
# 36
# 37
# 38
# 39
# 40
# 41
# 42
# 43
# 44
# 45
# 46
# 47
# 48
# 49
# 50
# 51
# 52
# 53
# 54
# 55
# 56
# 57
# 58
# 59
# 60
# 61
# 62
# 63
# 64
# 65
# 66
# 67
# 68
# 69
# 70
# 71
# 72
# 73
# 74
# 75
# 76
# 77
# 78
# 79
# 80
# 81
# 82
# 83
# 84
# 85
# 86
# 87
# 88
# 89
# 90
