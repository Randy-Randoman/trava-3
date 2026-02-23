# TRAVA 3 — Travel Planning with AI Agents + Excalidraw

AI-powered travel planning: chat with an agent, search real hotels on Booking.com with affiliate links, and build visual trip boards on an Excalidraw canvas.

**What's new vs trava-2:** LangGraph agent (swappable LLM), modular skills system, incremental board updates (append/remove instead of full replace), agent can read the board, Booking.com scraping with CJ affiliate links.

## Architecture

```
frontend/          Next.js 16 + React 19 + Tailwind (35% chat / 65% Excalidraw)
backend/           FastAPI + LangGraph agent
skills/            Modular tool packages (booking, board, web_search)
```

- **Frontend** — dashboard, chat panel, Excalidraw canvas. Copied from trava-2.
- **Backend** — FastAPI API, LangGraph ReAct agent, Supabase (Postgres + Auth).
- **Skills** — auto-discovered Python packages. Each exports `TOOLS` + `PROMPT`. Adding a skill = adding a folder.

See `architecture.md` for full details, `plan.md` for implementation phases.

## Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- A Supabase project (with migrations applied)

### 1. Environment

```bash
cp .env.example .env
# Fill in your keys (see .env.example for all vars)
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Playwright browsers (needed for Booking.com search)
playwright install chromium

# Start the server
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp ../.env .env.local   # Frontend needs NEXT_PUBLIC_* vars
npm run dev
```

Frontend: http://localhost:3000
Backend: http://localhost:8000

### 4. Database

Run migrations against your Supabase project (SQL Editor or CLI):

```
backend/migrations/001_initial_schema.sql
backend/migrations/002_rls_policies.sql
backend/migrations/003_chat_messages.sql
backend/migrations/004_revise_chat_schema.sql
backend/migrations/005_board_items.sql
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key (backend) |
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Same URL, for frontend |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Supabase anon key (frontend) |
| `GOOGLE_API_KEY` | For Gemini | langchain-google-genai |
| `ANTHROPIC_API_KEY` | For Claude | langchain-anthropic |
| `TAVILY_API_KEY` | For search | Web + image search |
| `CJ_PID` / `CJ_AID` | For affiliate | CJ Commission Junction |

## Project Structure

```
trava-3/
├── frontend/                   # Next.js app
│   └── src/
│       ├── app/                # Pages (home, dashboard, login)
│       ├── components/         # Canvas, chat, auth
│       ├── lib/                # API helpers, hooks, auth
│       └── types/              # TypeScript types
│
├── backend/                    # FastAPI app
│   ├── main.py                 # Entry point
│   ├── app/
│   │   ├── api/                # Routes (trips, chat)
│   │   ├── agent/              # LangGraph graph + state
│   │   ├── core/               # Config, prompts, templates
│   │   ├── logic/              # Transformer (Excalidraw generation)
│   │   ├── models/             # Pydantic schemas
│   │   └── services/           # Database, Playwright
│   └── migrations/             # SQL migrations (001-005)
│
├── skills/                     # Skill modules (auto-discovered)
│   ├── booking/                # Booking.com search + CJ affiliate
│   ├── board/                  # Board read/add/remove/clear
│   └── web_search/             # Tavily web + image search
│
├── .env                        # Secrets (not committed)
├── docker-compose.yml          # Docker setup
├── idea.md                     # Product vision
├── architecture.md             # Technical architecture
└── plan.md                     # Implementation plan + status
```
