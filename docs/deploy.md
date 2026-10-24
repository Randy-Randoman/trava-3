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

## Troubleshooting

- **CORS errors in the browser:** `ALLOWED_ORIGINS` on the backend must exactly match the frontend origin: scheme, host and port, with no trailing slash. The backend logs the allowed origins at startup.
- **Frontend calls the wrong backend URL:** `NEXT_PUBLIC_BACKEND_URL` was baked in at build time. Fix the variable and rebuild the frontend.
- **Booking search fails:** check the backend logs for `Failed to launch Playwright browser`.
