"""GitHub evidence collector: repos, languages, READMEs and representative source files."""
import base64
import os

import requests

GITHUB_API = "https://api.github.com"
MAX_REPOS = int(os.environ.get("MAX_GITHUB_REPOS", "15"))
CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".go", ".rs"}


def _headers(token=None):
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(url, token=None, **kwargs):
    r = requests.get(url, headers=_headers(token), timeout=20, **kwargs)
    r.raise_for_status()
    return r


def get_user_repos(username, token=None, max_repos=MAX_REPOS):
    return _get(
        f"{GITHUB_API}/users/{username}/repos",
        token,
        params={"per_page": max_repos, "sort": "updated", "type": "all"},
    ).json()


def get_repo_languages(languages_url, token=None):
    return _get(languages_url, token).json()


def get_readme_text(username, repo_name, token=None):
    r = requests.get(
        f"{GITHUB_API}/repos/{username}/{repo_name}/readme",
        headers=_headers(token),
        timeout=15,
    )
    if r.status_code != 200:
        return ""
    try:
        return base64.b64decode(r.json().get("content", "")).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def get_representative_code(username, repo, token=None, limit=2):
    """Fetch a few small source files from the default branch."""
    branch = repo.get("default_branch") or "main"
    r = requests.get(
        f"{GITHUB_API}/repos/{username}/{repo['name']}/git/trees/{branch}",
        headers=_headers(token),
        params={"recursive": "1"},
        timeout=20,
    )
    if r.status_code != 200:
        return []

    candidates = []
    for item in r.json().get("tree", []):
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        ext = os.path.splitext(path)[1].lower()
        if ext in CODE_EXTENSIONS and len(path) < 120:
            candidates.append(item)

    candidates.sort(key=lambda x: (len(x["path"].split("/")), len(x["path"])))
    out = []
    for item in candidates[:limit]:
        raw = requests.get(
            f"{GITHUB_API}/repos/{username}/{repo['name']}/contents/{item['path']}",
            headers=_headers(token),
            params={"ref": branch},
            timeout=15,
        )
        if raw.status_code != 200:
            continue
        try:
            content = base64.b64decode(raw.json().get("content", "")).decode("utf-8", errors="ignore")
        except Exception:
            continue
        if 100 <= len(content) <= 12000:
            out.append({"path": item["path"], "content": content[:12000]})
    return out


def build_github_profile(username, token=None, max_repos=MAX_REPOS):
    repos = get_user_repos(username, token, max_repos)
    profile = []
    for repo in repos:
        if repo.get("fork"):
            continue
        languages = get_repo_languages(repo["languages_url"], token)
        readme = get_readme_text(username, repo["name"], token)
        profile.append(
            {
                "name": repo["name"],
                "description": repo.get("description") or "",
                "languages": languages,
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "updated_at": repo.get("updated_at"),
                "default_branch": repo.get("default_branch"),
                "readme_excerpt": readme[:900],
                "code_samples": [
                    {"path": x.get("path"), "content": (x.get("content") or "")[:3000]}
                    for x in get_representative_code(username, repo, token)[:2]
                ],
            }
        )
    return {"username": username, "repos": profile}
