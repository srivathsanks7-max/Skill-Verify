# SkillVerify — Vercel deployment

This version uses Vercel's current zero-configuration Flask support. The Flask entrypoint is the root `app.py`; there are no Vercel rewrites and no `/api/index.py` function wrapper.

## Vercel settings

- Framework Preset: Flask
- Root Directory: `./`
- Build Command: `cd frontend && npm ci && npm run build`
- Output Directory: leave blank/default
- Install Command: leave default

## Environment variables

Set:
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GEMINI_API_KEY`
- `GEMINI_MODEL=gemini-2.5-flash`
- `FLASK_SECRET_KEY` (long random value)
- `COOKIE_SECURE=true`
- `FRONTEND_URL=https://YOUR-VERCEL-DOMAIN`
- `GITHUB_CALLBACK_URL=https://YOUR-VERCEL-DOMAIN/auth/github/callback`

The frontend and Flask backend use the same origin, so no separate API URL is needed.

## GitHub OAuth

Set Homepage URL to the Vercel deployment URL and callback URL to:
`https://YOUR-VERCEL-DOMAIN/auth/github/callback`

Redeploy after changing environment variables.
