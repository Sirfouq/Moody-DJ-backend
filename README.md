# MELODYSSEY — Backend

Flask API that turns a free-text *mood* into a real, playable Spotify playlist by
pairing an LLM music curator with the Spotify Web API.

Backend service for **[MELODYSSEY](https://melodyssey.vercel.app)** · client repo:
**[melodyssey-frontend](https://github.com/Sirfouq/melodyssey-frontend)**

## What it does

A vibe like *"rainy Sunday, slow coding session"* is sent to an **OpenAI model**
(strict JSON schema) which returns 15–20 real track recommendations. Each is resolved
to a concrete Spotify track via **Search**, then played in-browser via the Web
Playback SDK.

**Why an LLM?** Spotify deprecated its Recommendations and Audio Features endpoints
for new apps (late 2024), so the LLM is the recommendation engine and Spotify is just
the catalog + playback layer.

## Architecture

```
Browser ──> melodyssey.vercel.app ──(Vercel rewrite /api/*)──> Render (this Flask app)
                                                    ┌─────────────┴─────────────┐
                                                    ▼                           ▼
                                              OpenAI Responses API        Spotify Web API
```

Served **same-origin** (Vercel rewrites `/api/*` to Render), which keeps session
cookies first-party (`SameSite=Lax`) and avoids the third-party-cookie blocking in
Safari/Brave/Firefox — no CORS needed. Auth is Spotify **OAuth Authorization Code**
with a CSRF `state` and auto-refreshed tokens held in a signed, `HttpOnly` cookie.

## API

| Method | Path               | Auth | Description |
|--------|--------------------|------|-------------|
| GET    | `/api/login`       | —    | Redirect to Spotify authorize |
| GET    | `/api/callback`    | —    | OAuth callback; validates `state`, stores tokens |
| GET    | `/api/auth/status` | —    | `{ isLoggedIn, access_token }` (200) or 401 |
| GET    | `/api/me`          | ✅   | Spotify user profile |
| POST   | `/api/logout`      | ✅   | Clear session |
| POST   | `/api/generate`    | ✅   | `{ user_input, genre?, artist? }` → array of tracks |

Each `/api/generate` track: `{ name, artists[], uri, album_image_url, duration_ms }`.

## Tech stack

Python · Flask (gunicorn) · OpenAI SDK (structured outputs) · Spotify Web API ·
Pydantic · deployed on Render

## Run locally

```bash
pip install -r requirements.txt
python -m src.app        # http://127.0.0.1:5000
```

Requires a `.env` (gitignored) with `CLIENT_ID`, `CLIENT_SECRET`, `SECRET_KEY`,
`OPENAI_API_KEY`, `FRONTEND_URL`, and `SPOTIFY_REDIRECT_URI`. Run the frontend
alongside — its Vite dev server proxies `/api/*` here. In production, set
`FLASK_ENV=production` (enables Secure cookies) and pin `PYTHON_VERSION=3.13.4`.
