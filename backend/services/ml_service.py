import os
from pathlib import Path

import joblib


_model = None
_path = os.environ.get("SKILL_MODEL_PATH", "")
if _path and Path(_path).exists():
    try:
        _model = joblib.load(_path)
    except Exception:
        _model = None


def classify_evidence(text: str):
    if not _model or not text.strip():
        return None
    try:
        label = _model.predict([text])[0]
        probs = _model.predict_proba([text])[0]
        confidence = float(max(probs))
        return {"level": str(label), "confidence": round(confidence, 3)}
    except Exception:
        return None


def cross_check(profile: dict) -> dict:
    out = {}
    for skill, evidence in profile.get("evidence", {}).items():
        result = classify_evidence(evidence)
        if result:
            out[skill] = result
    return out
