import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "frontend" / "dist"

app = Flask(
    __name__,
    static_folder=str(DIST) if DIST.exists() else None,
    static_url_path="/",
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)

frontend_url = (
    os.environ.get("FRONTEND_URL")
    or os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
    or (f"https://{os.environ['VERCEL_URL']}" if os.environ.get("VERCEL_URL") else None)
    or os.environ.get("RENDER_EXTERNAL_URL")
    or "http://localhost:5173"
)
CORS(app, supports_credentials=True, origins=[frontend_url])

from routes.auth import auth_bp
from routes.api import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)


@app.get("/health")
def health():
    return {"status": "ok", "service": "skillverify"}


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    # API/auth routes are handled by their blueprints.
    if path.startswith(("api/", "auth/")):
        return {"error": "not found"}, 404
    if DIST.exists():
        candidate = DIST / path
        if path and candidate.is_file():
            return send_from_directory(DIST, path)
        return send_from_directory(DIST, "index.html")
    return (
        "Frontend has not been built. Run `cd frontend && npm install && npm run build`.",
        503,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
