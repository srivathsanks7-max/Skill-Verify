"""Gemini-powered analysis, question generation, review and career guidance."""
import json
import os
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=_api_key) if _api_key else None


class SkillProfile(BaseModel):
    skills: dict[str, str] = Field(default_factory=dict)
    evidence: dict[str, str] = Field(default_factory=dict)
    notes: str = ""


class TestCase(BaseModel):
    input: str
    expected_output: str


class CodingQuestion(BaseModel):
    title: str
    description: str
    difficulty: str
    skill_tested: str
    language: str
    starter_code: str
    test_cases: list[TestCase]


class DebugQuestion(BaseModel):
    title: str
    description: str
    difficulty: str
    skill_tested: str
    language: str
    buggy_code: str
    fixed_code: str
    test_cases: list[TestCase]
    bug_explanation: str


class ReviewQuestion(BaseModel):
    title: str
    description: str
    difficulty: str
    skill_tested: str
    language: str
    code: str
    issues: list[str]


class ExplanationGrade(BaseModel):
    score: int
    strengths: list[str]
    gaps: list[str]
    feedback: str


class JobMatch(BaseModel):
    requirements: list[str]
    evidence: dict[str, str]
    gaps: list[str]
    preparation: list[str]


class CareerPlan(BaseModel):
    actions: list[str] = Field(default_factory=list)
    summary: str = ""


def _require_client():
    if not client:
        raise RuntimeError("GEMINI_API_KEY is not configured.")


def _generate(prompt: str, schema: type[BaseModel]) -> BaseModel:
    _require_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.35,
        ),
    )
    return schema.model_validate_json(response.text)


def _compact_github_profile(github_profile: dict[str, Any], max_chars: int = 45000) -> dict[str, Any]:
    """Bound GitHub evidence before sending it to Gemini."""
    compact = {"username": github_profile.get("username"), "repos": []}
    for repo in (github_profile.get("repos") or [])[:8]:
        compact["repos"].append({
            "name": repo.get("name"),
            "description": (repo.get("description") or "")[:500],
            "languages": repo.get("languages") or {},
            "stars": repo.get("stars", 0),
            "readme_excerpt": (repo.get("readme_excerpt") or "")[:900],
            "code_samples": [
                {"path": x.get("path"), "content": (x.get("content") or "")[:2200]}
                for x in (repo.get("code_samples") or [])[:2]
            ],
        })
    while len(json.dumps(compact, ensure_ascii=False)) > max_chars and compact["repos"]:
        compact["repos"].pop()
    return compact


def analyze_skills(github_profile: dict, resume_text: str = "") -> dict:
    prompt = f"""You are a conservative technical skills analyst.
Infer evidence-backed engineering skills from the supplied GitHub evidence.
Do not treat a language appearing once as proof of mastery. Prefer repeated,
non-fork, substantive project evidence. If resume claims disagree with code
evidence, preserve the distinction in evidence.

Return levels only as beginner, intermediate, or advanced.
GitHub evidence:
{json.dumps(github_profile, indent=2)}

Optional resume claims:
{resume_text[:6000]}
"""
    return _generate(prompt, SkillProfile).model_dump()


def generate_question(skill_profile: dict, target_skill: str, language: str = "python") -> dict:
    prompt = f"""Create a practical coding verification question for the target skill
"{target_skill}" at the evidence level shown in this profile.
Use {language}. Include 5 deterministic stdin/stdout test cases. The starter
code must be executable as a complete program after the candidate fills it in.
Avoid external packages. Keep inputs and outputs simple enough for Judge0.

Profile:
{json.dumps(skill_profile, indent=2)}
"""
    return _generate(prompt, CodingQuestion).model_dump()


def generate_debug_question(github_profile: dict, skill_profile: dict, language: str = "python") -> dict:
    # Debugging is intentionally Python-first because the app can safely judge
    # the generated standalone program with the existing execution service.
    prompt = f"""Create a debugging assessment using the developer's own repository evidence.
Choose a small, representative Python function/program from the evidence
below and create a plausible single bug (or one tightly coupled bug cluster).
The candidate sees buggy_code and must fix it. fixed_code is the hidden answer.
Create 5 stdin/stdout test cases that distinguish the buggy and fixed behavior.
Do not use private secrets, credentials, or unrelated files.
Repository evidence:
{json.dumps(_compact_github_profile(github_profile), indent=2, ensure_ascii=False)}
Skill profile:
{json.dumps(skill_profile, indent=2)}
"""
    return _generate(prompt, DebugQuestion).model_dump()


def generate_review_question(github_profile: dict, skill_profile: dict, language: str = "python") -> dict:
    prompt = f"""Create a code-review assessment grounded in the developer's GitHub evidence.
Use Python and provide a short standalone snippet with exactly 2-4 meaningful
issues. Issues can be correctness, reliability, security, performance, testing,
or maintainability problems. Do not require external context. Return the
expected issue list as concise statements.
Evidence:
{json.dumps(_compact_github_profile(github_profile), indent=2, ensure_ascii=False)}
Profile:
{json.dumps(skill_profile, indent=2)}
"""
    return _generate(prompt, ReviewQuestion).model_dump()


def grade_explanation(question: dict, code: str, explanation: str) -> dict:
    prompt = f"""Grade a developer explanation after a coding verification task.
Use a 0-100 score. Reward correctness, reasoning, complexity awareness and
edge-case awareness. Do not reward confident wording without technical support.

Question:
{json.dumps(question, indent=2)}
Candidate code:
{code[:12000]}
Candidate explanation:
{explanation[:6000]}
"""
    return _generate(prompt, ExplanationGrade).model_dump()


def match_job(skill_profile: dict, github_profile: dict, job_description: str) -> dict:
    prompt = f"""Compare a job description with evidence-backed skills.
Do not infer protected traits or personal characteristics. Use only technical
requirements. For every requirement, label evidence as Strong, Moderate,
Weak evidence, or No evidence. Give concrete preparation actions for gaps.

Job description:
{job_description[:10000]}

Skill profile:
{json.dumps(skill_profile, indent=2)}

GitHub evidence:
{json.dumps(github_profile, indent=2)}
"""
    return _generate(prompt, JobMatch).model_dump()


def career_plan(skill_profile: dict, github_profile: dict) -> dict:
    prompt = f"""Create a concise 7-day technical improvement plan from actual evidence.
Prioritize concrete repository improvements and practice tasks. Avoid generic
course lists. Return the most useful actions, with a short reason for each.
Profile:
{json.dumps(skill_profile, indent=2)}
GitHub:
{json.dumps(github_profile, indent=2)}
"""
    return _generate(prompt, CareerPlan).model_dump()


def grade_review(question: dict, candidate_review: str) -> dict:
    class ReviewGrade(BaseModel):
        score: int
        found: list[str]
        missed: list[str]
        feedback: str

    prompt = f"""Grade this code review. Score 0-100 based on whether the candidate
identified the real technical issues, explained impact, and suggested sound fixes.

Expected issues:
{json.dumps(question.get('issues', []), indent=2)}

Code:
{question.get('code','')[:10000]}

Candidate review:
{candidate_review[:6000]}
"""
    return _generate(prompt, ReviewGrade).model_dump()
