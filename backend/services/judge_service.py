"""Hosted Judge0 adapter. No local Docker process is required."""
import os
import time

import requests

JUDGE0_URL = os.environ.get("JUDGE0_URL", "https://ce.judge0.com").rstrip("/")
RAPID_KEY = os.environ.get("JUDGE0_RAPIDAPI_KEY")
RAPID_HOST = os.environ.get("JUDGE0_RAPIDAPI_HOST")

LANGUAGE_IDS = {
    "python": 71,
    "javascript": 63,
    "java": 62,
    "c": 50,
    "cpp": 54,
    "go": 60,
    "rust": 73,
}


def _headers():
    headers = {"Content-Type": "application/json"}
    if RAPID_KEY:
        headers["X-RapidAPI-Key"] = RAPID_KEY
    if RAPID_HOST:
        headers["X-RapidAPI-Host"] = RAPID_HOST
    token = os.environ.get("JUDGE0_AUTH_TOKEN")
    if token:
        headers["X-Auth-Token"] = token
    return headers


def run_submission(source_code, language, stdin=""):
    language_id = LANGUAGE_IDS.get(language.lower())
    if language_id is None:
        raise ValueError(f"Unsupported language: {language}")

    r = requests.post(
        f"{JUDGE0_URL}/submissions?base64_encoded=false&wait=false",
        headers=_headers(),
        json={
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
            "cpu_time_limit": 3,
            "wall_time_limit": 5,
            "memory_limit": 128000,
        },
        timeout=20,
    )
    r.raise_for_status()
    token = r.json()["token"]

    for _ in range(30):
        result = requests.get(
            f"{JUDGE0_URL}/submissions/{token}?base64_encoded=false",
            headers=_headers(),
            timeout=20,
        ).json()
        if result.get("status", {}).get("id", 0) not in (1, 2):
            return result
        time.sleep(0.5)
    return {"error": "timeout waiting for judge service"}


def verify_solution(source_code, language, test_cases):
    results = []
    for case in test_cases:
        result = run_submission(source_code, language, case.get("input", ""))
        actual = (result.get("stdout") or "").strip()
        expected = str(case.get("expected_output", "")).strip()
        results.append(
            {
                "input": case.get("input", ""),
                "expected": expected,
                "actual": actual,
                "passed": actual == expected,
                "stderr": result.get("stderr") or result.get("compile_output"),
            }
        )
    passed = sum(r["passed"] for r in results)
    return {
        "total": len(results),
        "passed": passed,
        "all_passed": bool(results) and passed == len(results),
        "details": results,
    }
