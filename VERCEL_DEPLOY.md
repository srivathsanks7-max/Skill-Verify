# SkillVerify — Vercel deployment

## 1. Create a Vercel project
Import this repository into Vercel. Keep the project root as the repository root.

The included `vercel.json` builds the React app from `frontend/` and routes `/api/*`, `/auth/*`, and `/health` to the Flask serverless function.

## 2. Environment variables
Set these in Vercel for Production (and Preview if you want preview deployments to work):

- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GITHUB_CALLBACK_URL` = `https://YOUR-DOMAIN/auth/github/callback`
- `FRONTEND_URL` = `https://YOUR-DOMAIN`
- `GEMINI_API_KEY`
- `GEMINI_MODEL` = `gemini-2.5-flash`
- `FLASK_SECRET_KEY` = a long random secret
- `COOKIE_SECURE` = `true`
- `JUDGE0_URL` (if using Judge0)
- `JUDGE0_API_KEY` (if your Judge0 provider requires it)

## 3. GitHub OAuth
In GitHub Developer Settings → OAuth Apps, update the callback URL to the Vercel production domain:

`https://YOUR-DOMAIN/auth/github/callback`

## 4. Deploy
Vercel will run:

`cd frontend && npm ci && npm run build`

No Render service or local terminal is required after deployment.
