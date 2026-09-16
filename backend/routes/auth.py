import os
import secrets
from urllib.parse import urlencode

import requests
from flask import Blueprint, jsonify, redirect, request, session

auth_bp = Blueprint("auth", __name__)

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
FRONTEND_URL = (
    os.environ.get("FRONTEND_URL")
    or os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
    or (f"https://{os.environ['VERCEL_URL']}" if os.environ.get("VERCEL_URL") else None)
    or os.environ.get("RENDER_EXTERNAL_URL")
    or "http://localhost:5173"
)
GITHUB_CALLBACK_URL = (
    os.environ.get("GITHUB_CALLBACK_URL")
    or f"{FRONTEND_URL.rstrip('/')}/auth/github/callback"
)


@auth_bp.get("/auth/github/login")
def github_login():
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return jsonify({"error": "GitHub OAuth is not configured"}), 500

    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_CALLBACK_URL,
        "scope": "read:user,repo",
        "state": state,
    }
    return redirect("https://github.com/login/oauth/authorize?" + urlencode(params))


@auth_bp.get("/auth/github/callback")
def github_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        return jsonify({"error": "missing code from GitHub"}), 400
    if not state or not secrets.compare_digest(state, session.pop("oauth_state", "")):
        return jsonify({"error": "invalid OAuth state"}), 400

    token_resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        },
        timeout=15,
    )
    token_resp.raise_for_status()
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return jsonify({"error": "failed to get access token", "detail": token_data}), 400

    user_resp = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        timeout=15,
    )
    user_resp.raise_for_status()
    user = user_resp.json()

    session.clear()
    session["github_token"] = access_token
    session["github_username"] = user.get("login")
    session["github_avatar"] = user.get("avatar_url")
    session["github_name"] = user.get("name") or user.get("login")

    return redirect(f"{FRONTEND_URL.rstrip('/')}/dashboard")


@auth_bp.get("/auth/me")
def current_user():
    username = session.get("github_username")
    if not username:
        return jsonify({"logged_in": False})
    return jsonify(
        {
            "logged_in": True,
            "username": username,
            "name": session.get("github_name"),
            "avatar_url": session.get("github_avatar"),
        }
    )


@auth_bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})
