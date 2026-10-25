# Deploying TRAVA

TRAVA has two services: a FastAPI **backend** (`backend/`) and a Next.js **frontend** (`frontend/`). Both use Supabase for auth and data. You can run them:

- with **Docker Compose**, on your own machine or any VPS, or
- on **Railway**, as two services in one project.

Before you start, create a Supabase project and get your API keys (see [supabase-setup.md](supabase-setup.md) and [services-setup.md](services-setup.md)).

## Environment variables

| Variable | Service | Notes |
|---|---|---|
| `SUPABASE_URL` | backend | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | backend | `service_role` key. Keep it private |
| `LLM_PROVIDER` | backend | `google` (default) or `anthropic` |
| `GOOGLE_API_KEY` / `ANTHROPIC_API_KEY` | backend | Set the one for your provider |
| `TAVILY_API_KEY` | backend | Web and image search |
| `ALLOWED_ORIGINS` | backend | Comma-separated frontend URLs allowed by CORS, e.g. `https://trava.example.com` |
| `PUBLIC_BASE_URL` | backend | Public URL of the backend, exactly as agents are given it, e.g. `https://api.trava.example.com`. Defaults to `http://localhost:8000`. See [OAuth for agents](#oauth-for-agents) |
| `PORT` | backend | Defaults to `8000`. Railway sets it automatically |
| `NEXT_PUBLIC_SUPABASE_URL` | frontend | Same value as `SUPABASE_URL` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend | `anon public` key |
| `NEXT_PUBLIC_BACKEND_URL` | frontend | Public URL of the backend, as the browser sees it |

The backend reads `SUPABASE_URL`, and the frontend reads `NEXT_PUBLIC_SUPABASE_URL`. Both hold the same value, but you have to set both.

`NEXT_PUBLIC_*` variables are baked into the frontend **at build time**. If one is missing, the build fails. If you change one, rebuild the frontend.

## Docker Compose (local or VPS)

### Prerequisites

- Docker with the Compose plugin (`docker compose version`)
- The [Supabase CLI](https://supabase.com/docs/guides/cli), to apply migrations
- A Supabase project and API keys

### Steps

1. Create the root `.env`:

   ```bash
   cp .env.example .env
   ```

   Fill in every value. Compose reads this one file for both services.

2. On a VPS, point the URLs at your server instead of `localhost`. Add these to `.env`:

   ```bash
   NEXT_PUBLIC_BACKEND_URL=http://your-server:8000
   ALLOWED_ORIGINS=http://your-server:3000
   PUBLIC_BASE_URL=http://your-server:8000
   ```

   Locally, the defaults (`http://localhost:8000` and `http://localhost:3000`) already work.

3. Apply the database migrations:

   ```bash
   supabase link --project-ref <your-project-ref>
   supabase db push
   ```

4. Build and start both services:

   ```bash
   docker compose up --build
   ```

   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000/health should return `{"status":"ok"}`

5. In Supabase, go to **Authentication → URL Configuration**. Set the **Site URL** to your frontend URL and add it to **Redirect URLs**.

The backend image includes Chromium, so Booking.com search works inside the container.

## Railway

1. **Create the project.** In Railway, create a new project and choose **Deploy from GitHub repo**. Pick your fork of this repo.

2. **Create two services from the same repo:**
   - **backend**: in **Settings → Source**, set **Root Directory** to `backend`.
   - **frontend**: in **Settings → Source**, set **Root Directory** to `frontend`.

   Each folder has a `railway.toml`. Railway uses it to build from the folder's `Dockerfile` and to set the health check (`/health` for the backend, `/` for the frontend).

3. **Generate domains.** In each service, go to **Settings → Networking → Generate Domain**. You'll need both domains in the next step.

4. **Set the backend variables** in the backend's **Variables** tab:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
   - `LLM_PROVIDER`, plus `GOOGLE_API_KEY` or `ANTHROPIC_API_KEY`
   - `TAVILY_API_KEY`
   - `ALLOWED_ORIGINS=https://<frontend-domain>`
   - `PUBLIC_BASE_URL=https://<backend-domain>`

   Don't set `PORT`. Railway provides it.

5. **Set the frontend variables** in the frontend's **Variables** tab:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_BACKEND_URL=https://<backend-domain>`

   These must exist **before** the frontend builds. Railway passes service variables to the Docker build as build args. If you add or change one, redeploy the frontend so it rebuilds.

6. **Configure Supabase Auth.** In Supabase, go to **Authentication → URL Configuration**. Set the **Site URL** to `https://<frontend-domain>` and add it to **Redirect URLs**.

7. **Push the migrations** from your machine:

   ```bash
   supabase link --project-ref <your-project-ref>
   supabase db push
   ```

8. **Deploy both services** (or redeploy them after changing variables). Check that `https://<backend-domain>/health` returns `{"status":"ok"}`, then sign up on the frontend.

## OAuth for agents

The MCP server at `/mcp` is part of the backend service, so there's nothing extra to deploy. How to connect a client: [README](../README.md#using-with-claude-code--mcp).

External agents (Claude Code, Claude Cowork, claude.ai, ChatGPT) connect to TRAVA with OAuth 2.1. Supabase Auth is the authorization server: it registers the clients, runs the sign-in and issues the tokens. TRAVA hosts the consent page (`/oauth/consent`) and is the resource server. Users see and disconnect their agents under **Connected apps** on the dashboard.

The backend serves the protected resource metadata (RFC 9728) at `/.well-known/oauth-protected-resource` (and `…/mcp`). It names the resource `<PUBLIC_BASE_URL>/mcp`, which clients check against the URL they were given, so `PUBLIC_BASE_URL` must be the backend's public URL exactly. `/mcp` also only accepts requests whose `Host` header is `PUBLIC_BASE_URL`'s host (or `localhost`/`127.0.0.1`); any other host gets HTTP 421. If you use a custom domain, set `PUBLIC_BASE_URL` to it.

### Supabase project settings (made by hand)

Nothing in the repo applies these.

1. **Authentication → OAuth Server: enable the OAuth 2.1 server.**
2. On the same page, set the **Authorization path** to `/oauth/consent`. Supabase joins it to the Site URL, so the Site URL must be the frontend URL (see the steps above).
3. On the same page, turn on **Allow dynamic client registration**. Agents register themselves; a client gets nothing until a user signs in and presses Allow.
4. **Project Settings → JWT Keys: the current signing key must be asymmetric** (ES256 or RS256). The backend verifies agent tokens against the project's JWKS and can't verify HS256 tokens.

The token issuer is `<SUPABASE_URL>/auth/v1`. If you add a Supabase custom domain, the issuer changes with it, so set the backend's `SUPABASE_URL` to the custom domain at the same time, or every agent is refused.

### Migrations

Agents need migrations `20260101000009_agent_grants.sql` (the grant check below) and `20260101000010_canvas_realtime.sql` (open boards reload when an agent changes them, via Supabase Realtime). `supabase db push` applies both.

Access tokens live as long as the project's JWT expiry, but disconnecting an app takes effect at once: on every agent request the backend checks the token's issuer, audience and `client_id`, then calls `public.agent_grant_active` (migration `20260101000009_agent_grants.sql`) to check that the consent isn't revoked, the client isn't deleted and the session still exists.

### Verify the agent connection (once, after a deploy)

1. `curl -i -X POST <PUBLIC_BASE_URL>/mcp` answers `401` with a `WWW-Authenticate` header naming `resource_metadata`, and that URL answers JSON naming `<SUPABASE_URL>/auth/v1`.
2. **Claude Code:** `claude mcp add --transport http trava <PUBLIC_BASE_URL>/mcp`, start a session, run `/mcp`, pick `trava`, Authenticate; log in, press Allow. Ask it to list your trips.
3. **claude.ai** and **ChatGPT:** connect as described in the [README](../README.md#using-with-claude-code--mcp) and call a tool in a chat.
4. Disconnect one client under **Connected apps**; its next call fails with `401`.

If the consent page says the request expired or was already used on a fresh connect, it's likely the open Supabase bug [supabase/auth#2820](https://github.com/supabase/auth/issues/2820).

## Troubleshooting

- **CORS errors in the browser:** `ALLOWED_ORIGINS` on the backend must exactly match the frontend origin: scheme, host and port, with no trailing slash. The backend logs the allowed origins at startup.
- **Frontend calls the wrong backend URL:** `NEXT_PUBLIC_BACKEND_URL` was baked in at build time. Fix the variable and rebuild the frontend.
- **`/mcp` returns 421 Misdirected Request:** the request's `Host` doesn't match `PUBLIC_BASE_URL`. Set it to the exact public domain the client uses.
- **Booking search fails:** check the backend logs for `Failed to launch Playwright browser`.
