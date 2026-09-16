# OAuth fix

This version uses Vercel's `VERCEL_PROJECT_PRODUCTION_URL` for GitHub OAuth callbacks.
Do not set `GITHUB_CALLBACK_URL`. Register the production callback in GitHub:
`https://skillverifyf.vercel.app/auth/github/callback`
