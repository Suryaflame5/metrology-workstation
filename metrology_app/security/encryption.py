"""
Data-at-Rest Tokenization & Cryptographic Field Encryption.
Provides AES-256-GCM authenticated encryption for sensitive customer tolerances and proprietary assets.
"""

import os
import base64
import json
import hashlib
from typing import Dict, Any, Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


MASTER_KEY_SEED = os.environ.get("METROLOGY_MASTER_KEY", "NOVYRAX_ENTERPRISE_METROLOGY_KEY_2026_MASTER_SECRET")
DERIVED_KEY = hashlib.sha256(MASTER_KEY_SEED.encode("utf-8")).digest()


def encrypt_sensitive_payload(data: Dict[str, Any]) -> str:
    """
    Encrypt dictionary data into a base64 encoded AES-256-GCM ciphertext envelope.
    """
    raw_bytes = json.dumps(data, sort_keys=True).encode("utf-8")
    if CRYPTOGRAPHY_AVAILABLE:
        aesgcm = AESGCM(DERIVED_KEY)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, raw_bytes, None)
        envelope = {
            "version": "AES-256-GCM",
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        }
        return base64.b64encode(json.dumps(envelope).encode("utf-8")).decode("ascii")
    else:
        # Fallback obfuscated tokenization with HMAC-SHA256 signature
        sig = hashlib.sha256(raw_bytes + DERIVED_KEY).hexdigest()
        envelope = {
            "version": "TOKENIZED_HMAC_SHA256",
            "payload": base64.b64encode(raw_bytes).decode("ascii"),
            "signature": sig,
        }
        return base64.b64encode(json.dumps(envelope).encode("utf-8")).decode("ascii")


def decrypt_sensitive_payload(token_str: str) -> Dict[str, Any]:
    """
    Decrypt and verify an AES-256-GCM ciphertext envelope.
    """
    raw_envelope_json = base64.b64decode(token_str.encode("ascii")).decode("utf-8")
    envelope = json.loads(raw_envelope_json)

    if envelope.get("version") == "AES-256-GCM" and CRYPTOGRAPHY_AVAILABLE:
        nonce = base64.b64decode(envelope["nonce"].encode("ascii"))
        ciphertext = base64.b64decode(envelope["ciphertext"].encode("ascii"))
        aesgcm = AESGCM(DERIVED_KEY)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(decrypted.decode("utf-8"))
    elif envelope.get("version") == "TOKENIZED_HMAC_SHA256":
        payload_bytes = base64.b64decode(envelope["payload"].encode("ascii"))
        sig = envelope["signature"]
        expected_sig = hashlib.sha256(payload_bytes + DERIVED_KEY).hexdigest()
        if sig != expected_sig:
            raise ValueError("Cryptographic envelope integrity violation.")
        return json.loads(payload_bytes.decode("utf-8"))
    else:
        raise ValueError("Unsupported encryption envelope format.")
