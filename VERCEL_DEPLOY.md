# SkillVerify — Vercel deployment

This version uses Vercel native Flask support. Vercel detects the root `app.py`; there are no `/api` rewrites. The Flask app serves the built React frontend from `frontend/dist`.

## Vercel settings
- Framework Preset: Flask
- Root Directory: `.`
- Build Command: `cd frontend && npm ci && npm run build`
- Output Directory: leave blank
- Install Command: default

## Environment variables
Set `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `FLASK_SECRET_KEY`, `COOKIE_SECURE`, `FRONTEND_URL`, and `GITHUB_CALLBACK_URL`.

For production, use your Vercel domain for `FRONTEND_URL` and `GITHUB_CALLBACK_URL`.


## V7 OAuth fix

GitHub OAuth now derives the callback URL from the actual Vercel host used for the request, so preview and production URLs do not accidentally get mixed. `GITHUB_CALLBACK_URL` is optional; if set, it must exactly match the deployment domain.
