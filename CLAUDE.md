- Simplicity wins over cleverness. Ask for clarification, we are a team. Don't over-engineer.
- **`docs/plan.md`** is for making a plan and editing it

## Commands

### Start the app (two terminals)

Terminal 1 — Backend (http://localhost:8000):
```bash
cd backend && source .venv/bin/activate && uvicorn main:app --reload
```

Terminal 2 — Frontend (http://localhost:3000):
```bash
cd frontend && npm run dev
```

### Backend setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium       # Needed for Booking.com scraping
```

### Frontend setup
```bash
cd frontend
npm install
ln -s ../.env .env.local          # Symlink to root .env
```

### Other frontend commands
```bash
cd frontend
npm run build        # Production build
npm run lint         # Run linter
```

### Run tests
```bash
# All unit tests (from project root, venv must be active)
python -m pytest tests/unit/ -v

# Specific test file
python -m pytest tests/unit/test_url_builder.py -v

# With short summary
python -m pytest tests/unit/ --tb=short
```

Config: `pytest.ini` at project root. Tests live in `tests/unit/`. Skills are on `pythonpath` via pytest config.

### Environment
- Root `.env` has all secrets (see `.env.example`)
- Frontend symlinks `.env.local -> ../.env` (already set up)
- Backend loads `.env` from project root automatically

### Database
- Supabase project — migrations in `backend/migrations/001-005.sql`
- Run via Supabase SQL Editor or CLI

## Key conventions
- Backend: FastAPI + Python, Pydantic models, async endpoints
- Frontend: Next.js 16 + React 19 + Tailwind, App Router
- Skills: each skill is a Python package in root `skills/` — exports `TOOLS` list and `PROMPT` string
- Agent: LangGraph ReAct pattern, swappable LLM (Gemini default, Anthropic optional)