# SkillVerify — evidence-backed technical career copilot

This upgraded version turns the original GitHub skill quiz into a single full-stack app:

- GitHub OAuth + repository evidence
- Gemini-powered skill analysis (Google GenAI SDK + structured JSON)
- Adaptive assessment: coding, debugging your own-code style challenge, and code review
- Explanation grading after passing a coding/debugging challenge
- Claimed-vs-evidence skill context when a resume is supplied
- Job-description → evidence map and gap preparation
- 7-day technical improvement plan
- Signed shareable verification credential with a 90-day shelf-life
- Hosted Judge0 adapter so no local Docker/Judge0 terminal is required
- React/Vite frontend is built into Flask and served from the same public URL
- Google Colab notebook for training a separate skill-level classifier/calibrator

## Local run

1. Copy `backend/env.example` to `backend/.env` and fill in secrets.
2. Create a GitHub OAuth App:
   - local callback: `http://localhost:5000/auth/github/callback`
   - production callback: your deployed URL + `/auth/github/callback`
3. Install:
   `pip install -r backend/requirements.txt`
4. Build frontend:
   `cd frontend && npm ci && npm run build`
5. Start one server:
   `gunicorn --chdir backend --bind 0.0.0.0:5000 app:app`
6. Open `http://localhost:5000`.

For local development with Vite, `npm run dev` still works, but the production architecture does not require a separate frontend server.

## Hosted deployment

Render can deploy this repository as one Python web service. The `render.yaml` file already contains the build/start commands. Render provides an `onrender.com` HTTPS URL and can run the Flask app with Gunicorn. Add the environment secrets in the Render dashboard.

Important: the hosted Judge0 endpoint may have quota/authentication requirements. If using RapidAPI Judge0, set both `JUDGE0_RAPIDAPI_KEY` and `JUDGE0_RAPIDAPI_HOST`.

## Gemini

The original OpenAI calls have been replaced by Gemini. The backend uses `GEMINI_API_KEY` and `GEMINI_MODEL` (default `gemini-2.5-flash`).

## Colab

Open `colab/skillverify_model_training.ipynb`. It trains a lightweight skill-level classifier from labeled examples and exports `skill_model.joblib`. The notebook includes a synthetic bootstrap dataset only for demonstrating the pipeline; replace it with real labeled assessment data before treating model outputs as evidence.

## Security/production notes

- OAuth state validation is enabled.
- Secrets are environment variables, never committed.
- Private GitHub tokens stay in the server-side session and are not sent to the browser.
- The credential is HMAC-signed.
- Candidate source code is executed by Judge0 with CPU/memory limits.
- The current demo stores active assessments in process memory. For a multi-instance production deployment, move sessions/results/credentials to Postgres + Redis.
- Do not commit the original `.env`, `node_modules`, or Python virtual environment from the supplied ZIP.
