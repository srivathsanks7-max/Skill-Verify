import hashlib
import hmac
import json
import os
import time
import uuid

_STORE = {}
SECRET = os.environ.get("CREDENTIAL_SIGNING_SECRET", "change-me")
SHELF_DAYS = int(os.environ.get("VERIFICATION_SHELF_LIFE_DAYS", "90"))


def issue(username, skill_profile, score):
    issued_at = int(time.time())
    expires_at = issued_at + SHELF_DAYS * 86400
    payload = {
        "id": str(uuid.uuid4()),
        "username": username,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "shelf_life_days": SHELF_DAYS,
        "skills": skill_profile.get("skills", {}),
        "score_percent": score.get("score_percent", 0),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(SECRET.encode(), canonical, hashlib.sha256).hexdigest()
    payload["signature"] = signature
    _STORE[payload["id"]] = payload
    return payload


def get(credential_id):
    return _STORE.get(credential_id)


def verify(payload):
    signature = payload.get("signature", "")
    data = {k: v for k, v in payload.items() if k != "signature"}
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    expected = hmac.new(SECRET.encode(), canonical, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
