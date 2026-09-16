import html
import uuid

from flask import Blueprint, jsonify, request, session

from services import ai_service, credential_service, github_service, judge_service, ml_service

api_bp = Blueprint("api", __name__)

_active_questions = {}
_results = {}
_profiles = {}

QUESTION_COUNT = 3


def _user():
    return session.get("github_username")


def _require_user():
    username = _user()
    if not username:
        return None, (jsonify({"error": "not logged in"}), 401)
    return username, None


@api_bp.post("/api/start-test")
def start_test():
    username, err = _require_user()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    source_mode = body.get("source_mode", "github")
    assessment_mode = body.get("assessment_mode", "adaptive")
    language = body.get("language", "python")
    resume_text = body.get("resume_text", "")

    if source_mode == "manual":
        manual_skills = body.get("skills", {})
        if not manual_skills:
            return jsonify({"error": "no skills provided"}), 400
        skill_profile = {
            "skills": manual_skills,
            "evidence": {k: "self-reported" for k in manual_skills},
            "notes": "Self-reported starting profile; verification is based on assessment results.",
        }
        github_profile = {"username": username, "repos": []}
    else:
        try:
            github_profile = github_service.build_github_profile(username, session.get("github_token"))
            skill_profile = ai_service.analyze_skills(github_profile, resume_text)
            skill_profile["model_cross_check"] = ml_service.cross_check(skill_profile)
        except Exception as exc:
            return jsonify({"error": "GitHub/AI analysis failed", "detail": str(exc)}), 502

    try:
        skills = list(skill_profile.get("skills", {}))
        target_skills = skills[:3] or ["general programming", "debugging", "code quality"]
        questions = []

        if assessment_mode in ("adaptive", "debug"):
            if source_mode != "manual":
                questions.append(
                    ai_service.generate_debug_question(github_profile, skill_profile, language)
                )

        if assessment_mode in ("adaptive", "coding"):
            for skill in target_skills[:2 if assessment_mode == "adaptive" else 3]:
                questions.append(ai_service.generate_question(skill_profile, skill, language))

        if assessment_mode in ("adaptive", "review"):
            if source_mode != "manual":
                questions.append(ai_service.generate_review_question(github_profile, skill_profile, language))

        questions = questions[:QUESTION_COUNT]
        if not questions:
            return jsonify({"error": "question generation failed"}), 502
    except Exception as exc:
        return jsonify({"error": "question generation failed", "detail": str(exc)}), 502

    stored = {}
    safe_questions = []
    for q in questions:
        qid = str(uuid.uuid4())
        q["id"] = qid
        q["assessment_type"] = (
            "debug" if "buggy_code" in q else "review" if "issues" in q else "coding"
        )
        stored[qid] = q

        safe = {k: v for k, v in q.items() if k not in ("test_cases", "fixed_code", "issues")}
        safe["id"] = qid
        safe["test_case_inputs"] = [tc["input"] for tc in q.get("test_cases", [])]
        safe_questions.append(safe)

    _active_questions[username] = stored
    _results[username] = {}
    _profiles[username] = {"skill_profile": skill_profile, "github_profile": github_profile}

    return jsonify({"skill_profile": skill_profile, "questions": safe_questions})


@api_bp.post("/api/submit")
def submit_solution():
    username, err = _require_user()
    if err:
        return err
    questions = _active_questions.get(username, {})
    body = request.get_json(silent=True) or {}
    qid = body.get("question_id")
    code = body.get("source_code")
    language = body.get("language", "python")

    if qid not in questions or not code:
        return jsonify({"error": "invalid question or source code"}), 400

    q = questions[qid]
    if q.get("assessment_type") == "review":
        return jsonify({"error": "Use the review endpoint for review assessments."}), 400

    result = judge_service.verify_solution(code, language, q.get("test_cases", []))
    _results.setdefault(username, {})[qid] = {"kind": q["assessment_type"], "judge": result, "code": code}
    return jsonify(result)


@api_bp.post("/api/explanation")
def explanation():
    username, err = _require_user()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    qid = body.get("question_id")
    explanation_text = body.get("explanation", "")
    if qid not in _active_questions or qid not in _active_questions[username] or not explanation_text.strip():
        return jsonify({"error": "question_id and explanation are required"}), 400

    q = _active_questions[username][qid]
    code = _results.get(username, {}).get(qid, {}).get("code", "")
    grade = ai_service.grade_explanation(q, code, explanation_text)
    _results[username].setdefault(qid, {})["explanation"] = grade
    return jsonify(grade)


@api_bp.post("/api/review")
def review():
    username, err = _require_user()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    qid = body.get("question_id")
    candidate_review = body.get("review", "")
    if qid not in _active_questions.get(username, {}) or not candidate_review.strip():
        return jsonify({"error": "question_id and review are required"}), 400
    q = _active_questions[username][qid]
    grade = ai_service.grade_review(q, candidate_review)
    _results.setdefault(username, {})[qid] = {"kind": "review", "review": grade}
    return jsonify(grade)


@api_bp.get("/api/score")
def get_score():
    username, err = _require_user()
    if err:
        return err
    questions = _active_questions.get(username, {})
    results = _results.get(username, {})

    components = []
    for qid, result in results.items():
        if "judge" in result:
            judge = result["judge"]
            code_score = (judge.get("passed", 0) / judge.get("total", 1)) * 100
            explanation_score = result.get("explanation", {}).get("score")
            final = code_score if explanation_score is None else code_score * 0.8 + explanation_score * 0.2
            components.append(final)
        elif result.get("review"):
            components.append(result["review"].get("score", 0))

    score_percent = round(sum(components) / len(components)) if components else 0
    total_cases = sum(r.get("judge", {}).get("total", 0) for r in results.values())
    passed_cases = sum(r.get("judge", {}).get("passed", 0) for r in results.values())
    fully_passed = sum(
        1 for r in results.values()
        if r.get("judge", {}).get("all_passed") or r.get("review", {}).get("score", 0) >= 80
    )
    return jsonify(
        {
            "total_questions": len(questions),
            "attempted_questions": len(results),
            "questions_fully_passed": fully_passed,
            "total_test_cases": total_cases,
            "passed_test_cases": passed_cases,
            "score_percent": score_percent,
            "components": components,
        }
    )


@api_bp.post("/api/credential")
def credential():
    username, err = _require_user()
    if err:
        return err
    score = get_score().json
    profile = _profiles.get(username, {}).get("skill_profile", {})
    if not profile:
        return jsonify({"error": "run an assessment first"}), 400
    return jsonify(credential_service.issue(username, profile, score))


@api_bp.post("/api/job-match")
def job_match():
    username, err = _require_user()
    if err:
        return err
    job = (request.get_json(silent=True) or {}).get("job_description", "")
    profile = _profiles.get(username)
    if not profile or not job.strip():
        return jsonify({"error": "run GitHub analysis and provide a job description"}), 400
    try:
        return jsonify(ai_service.match_job(profile["skill_profile"], profile["github_profile"], job))
    except Exception as exc:
        return jsonify({"error": "job analysis failed", "detail": str(exc)}), 502


@api_bp.get("/api/career-plan")
def career_plan():
    username, err = _require_user()
    if err:
        return err
    profile = _profiles.get(username)
    if not profile:
        return jsonify({"error": "run GitHub analysis first"}), 400
    try:
        return jsonify(ai_service.career_plan(profile["skill_profile"], profile["github_profile"]))
    except Exception as exc:
        return jsonify({"error": "career plan failed", "detail": str(exc)}), 502


@api_bp.get("/verify/<credential_id>")
def verify_credential(credential_id):
    cred = credential_service.get(credential_id)
    if not cred or not credential_service.verify(cred):
        return "Credential not found or signature invalid.", 404

    skills = "".join(
        f"<li><strong>{html.escape(k)}</strong> — {html.escape(v)}</li>"
        for k, v in cred.get("skills", {}).items()
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>SkillVerify credential</title>
<style>
body{{font-family:Inter,system-ui;background:#0b1020;color:#eef2ff;display:grid;place-items:center;min-height:100vh;margin:0}}
.card{{max-width:620px;width:calc(100% - 32px);padding:36px;border:1px solid #273354;border-radius:24px;background:linear-gradient(145deg,#151d38,#10172b);box-shadow:0 30px 80px #0006}}
.badge{{display:inline-block;padding:7px 11px;border-radius:999px;background:#19d3ae22;color:#55e0c2;font-size:12px;font-weight:700}}
h1{{font-size:32px;margin:16px 0 8px}}p{{color:#a9b4d0;line-height:1.6}}ul{{padding-left:20px;line-height:2}}
</style></head><body><main class="card">
<span class="badge">✓ SIGNED VERIFICATION</span>
<h1>{html.escape(cred["username"])}'s technical verification</h1>
<p>Verified skills and assessment evidence issued by SkillVerify.</p>
<ul>{skills}</ul>
<p>Assessment score: <strong>{cred["score_percent"]}%</strong><br>
Issued: {cred["issued_at"]}<br>Verification shelf life: {cred["shelf_life_days"]} days.</p>
</main></body></html>"""
