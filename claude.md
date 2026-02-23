- Simplicity wins over cleverness. Ask for clarification, we are a team. Don't over-engineer.
- **`plan.md`** is for making a plan and editing it
- **`idea.md`** is the overall idea
- **`architecture.md`** is the full technical architecture
- **`learning.md`** has learnings from trava-2

## Commands

### Backend
```bash
cd backend
source .venv/bin/activate         # Activate venv
uvicorn main:app --reload         # Start dev server (port 8000)
pip install -r requirements.txt   # Install/update deps
playwright install chromium       # Install browser for Booking.com scraping
```

### Frontend
```bash
cd frontend
npm install          # Install deps
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run lint         # Run linter
```

### Environment
- Root `.env` has all secrets (see `.env.example`)
- Frontend needs `cp ../.env .env.local` (or symlink) for `NEXT_PUBLIC_*` vars
- Backend loads `.env` from project root automatically

### Database
- Supabase project — migrations in `backend/migrations/001-005.sql`
- Run via Supabase SQL Editor or CLI

## Key conventions
- Backend: FastAPI + Python, Pydantic models, async endpoints
- Frontend: Next.js 16 + React 19 + Tailwind, App Router
- Skills: each skill is a Python package in root `skills/` — exports `TOOLS` list and `PROMPT` string
- Agent: LangGraph ReAct pattern, swappable LLM (Gemini default, Anthropic optional)
- trava-2 source (for reference): `/Users/hoeherp/development/playground/github/trava-2/Untitled/`
