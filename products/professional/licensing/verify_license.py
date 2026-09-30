import sys
import json
import hmac
import hashlib

VERIFY_KEY = b"MW_PUB_VERIFY_KEY_2026_PRECISION_METROLOGY_981247"

def verify_license(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sig = data.pop("signature", "")
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    computed = hmac.new(VERIFY_KEY, raw, hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig, computed):
        print(f"VALID: License is authentic for {data.get('customer_name')} ({data.get('plan_id')})")
        return True
    else:
        print("INVALID: Signature mismatch or corrupted license file.")
        return False

if __name__ == "__main__":
    f = sys.argv[1] if len(sys.argv) > 1 else "calibra-license.json"
    verify_license(f)
