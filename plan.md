# Plan: trava-3 Implementation

## Vision

Same UI as trava-2 (dashboard, chat, Excalidraw) but with a new agent backend: LangGraph + skills system, incremental board management, Booking.com search with affiliate links.

**MVP:** User chats → agent searches Booking.com → returns real hotels with affiliate links → user uses "add to board" button or calls it in chat → hotels appear as cards on Excalidraw canvas → user can iterate (add more, remove, replace).

---

## Decisions Made

| Topic | Decision | Rationale |
|-------|----------|-----------|
| **Repo** | New repo (trava-3) | Clean start, new architecture |
| **Frontend** | Copy from trava-2 | Works well, minimal changes needed |
| **Agent** | LangGraph (ReAct) | LLM-agnostic, composable |
| **LLM** | Swappable (Gemini default, Anthropic optional) | Both supported via langchain, configured by env var |
| **Skills** | Python packages at root `skills/`, auto-discovered | Easy to add new skills, signals future independence |
| **Board** | Incremental (append/remove) | Fixes trava-2's full-replace problem |
| **Board state** | board_items JSONB on trips | Agent can read what's on the board |
| **Hotel search** | Playwright + Booking.com | Real results, real links |
| **Affiliate** | CJ deep links | Revenue on every booking |
| **DB** | Supabase (same schema + board_items) | Proven, reusable |

---

## Phase 1: Scaffold + Copy ✅ DONE

**Goal:** Get the app shell running — frontend renders, backend starts, DB connects. No agent yet.

**Status:** Completed 2025-02-23. All files copied, adapted, and verified.

### What was done

**Frontend** (33 files copied from trava-2):
- All components, hooks, types, configs copied as-is
- `useChat.ts` adapted: `board_data` handler → `canvas_updated` (server-side transform)
- `api.ts` cleaned: removed dead `transformBoardData` function (endpoint no longer exists)
- `supabase/client.ts`: added safe fallback for missing env vars (build-time safety)
- `next build` passes cleanly

**Backend** (27 files):
- `trips.py`: copied, `/trips/transform` endpoint removed
- `transformer.py`: copied, `amadeus` imports replaced with local `validate_url`/`sanitize_url` helpers
- `config.py`: adapted with `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `CJ_PID`, `CJ_AID`
- `main.py`: adapted, Gemini/feedback imports removed, chat router mounted
- `chat.py`: stub (501), `agent/graph.py` + `agent/state.py`: stubs
- `database.py`, `templates.py`, `models/`, `migrations/001-004`: copied as-is

**Infrastructure:**
- `docker-compose.yml`, `.env.example`, `.gitignore`
- `skills/` at root with registry (`load_all_skills()`) + 3 skill stubs (booking, board, web_search)
- `migrations/005_board_items.sql` — board_items JSONB column
- `requirements.txt` with all deps (fastapi, langgraph, langchain-google-genai, langchain-anthropic, playwright, tavily-python)

### Verified
- [x] `next build` — compiles, all routes render
- [x] `uvicorn main:app` — starts, `/health` returns `{"status":"ok"}`
- [x] All routes registered (trips CRUD, canvas, chat stubs)
- [x] Supabase env vars load correctly
- [x] Create a trip → welcome canvas appears
- [x] Excalidraw renders with scrollToContent
- [x] Dashboard scrolls, trip cards work
- [x] Auth works (login/logout, stale token handling)
- [x] Logo displays correctly

### Fixes applied after initial scaffold
- `public/` dir was missing — copied `trava-logo.png` + `excalidraw.css` from trava-2
- Logo was mirrored — removed `scale-x-[-1]` from page.tsx, ChatInterface.tsx, dashboard
- Board was over-zoomed — added `scrollToContent: true` to BoardWrapper initialData
- Dashboard couldn't scroll — removed `overflow: hidden` from global body CSS (trip editor already constrains itself)
- Auth token errors — AuthContext now handles stale refresh tokens gracefully (clears + redirects to login)
- Chat messages 501 — useChat handles non-OK responses from stub endpoint without throwing
- Chat send still returns 501 — expected, this is Phase 2 work (agent not implemented yet)

---

## Phase 2: Skills + Agent ✅ DONE

**Goal:** Agent can chat and call tools. Skills are loaded from the registry.

**Status:** Completed 2026-02-24. All 6 issues implemented and verified.

**Tracked in GitHub Issues:** https://github.com/Randy-Randoman/trava-3/issues

| # | Issue | Description | Status |
|---|-------|-------------|--------|
| #1 | LangGraph agent: state, graph, system prompt | Agent core — ReAct graph, swappable LLM (Gemini default), dynamic prompt | ✅ |
| #2 | Chat endpoint: SSE streaming with LangGraph | Rewrote chat.py with real SSE streaming, message persistence | ✅ |
| #3 | Playwright service: shared headless browser | Singleton browser manager with graceful shutdown | ✅ |
| #4 | Booking skill: search + CJ affiliate links | Playwright scraping, deeplink generation, @tool wrappers | ✅ |
| #5 | Web search skill: Tavily integration | Web + image search @tools | ✅ |
| #6 | Board skill: stub tool implementations | Placeholder tools + BoardItem model for Phase 3 | ✅ |

### What was built

**Agent (8 tools loaded):**
- `AgentState` TypedDict with messages, trip_id, user_id
- LangGraph ReAct graph: START → agent → should_continue? → tools (loop) or END
- Swappable LLM: Gemini (default, gemini-2.5-flash) or Anthropic (claude-sonnet-4.6)
- Dynamic system prompt with skill prompts injected

**Chat endpoint:**
- `POST /chat/stream` — SSE streaming with status/text/error/done events
- `GET /chat/messages/{trip_id}` — message history from DB
- Content extraction handles both string and structured (Gemini) responses

**Skills:**
- `booking_search`, `deeplink_generate` — Playwright-based Booking.com scraping + CJ affiliate links
- `web_search`, `image_search` — Tavily API integration
- `board_read`, `board_add_items`, `board_remove_items`, `board_clear` — stubs for Phase 3

**Infrastructure:**
- Playwright singleton service with async context manager
- App lifespan handler for clean browser shutdown
- Frontend error handling fix (useChat.ts no longer swallows error events)

### Verified
- [x] Chat with agent — get a response
- [x] SSE streaming works (status updates, text response, done)
- [x] 8 tools auto-discovered by skills registry
- [x] Agent graph compiles and runs with all tools bound
- [x] Board tools return stub messages (Phase 3 will wire them to canvas)

### Fixes applied after initial implementation
- `search.py`: lazy import of `app.services.playwright` (skills load from repo root, `app` only on path at runtime)
- `chat.py`: `_extract_text()` handles Gemini's list-of-content-blocks response format
- `useChat.ts`: inner catch only swallows `SyntaxError` (JSON parse), re-throws real errors
- Model updated from deprecated `gemini-2.0-flash` to `gemini-3-flash-preview`

---

## Phase 3: Board Intelligence ✅ DONE

**Goal:** Agent can read, add to, remove from, and clear the board. Canvas updates incrementally.

**Status:** Completed 2026-02-24. All 4 issues implemented and verified.

| # | Issue | Description | Status |
|---|-------|-------------|--------|
| #7 | Database: board_items column + read/write | Migration + DatabaseService methods | ✅ |
| #8 | Transformer: generate_card_elements() | Incremental card placement below existing content | ✅ |
| #9 | Board tools: wire to canvas | Replace stubs with real read/add/remove/clear | ✅ |
| #10 | SSE: canvas_updated from board tools | Emit event so frontend reloads canvas | ✅ |

### What was built
- `get_board_items()` / `update_board_items()` on DatabaseService
- `generate_card_elements()` in transformer — masonry layout below existing content
- All 4 board tools wired: board_read, board_add_items, board_remove_items, board_clear
- `InjectedState("trip_id")` on all board tools — trip_id injected from agent state, not hallucinated by LLM
- `canvas_updated` SSE event emitted after board-mutating tools run

### Verified
- [x] Board add/remove/read/clear works end-to-end
- [x] Canvas updates live via SSE
- [x] Cards appear on Excalidraw with masonry layout
- [x] Multiple add rounds stack below previous cards

### Fixes applied
- Board tools originally took `trip_id` as a normal param — LLM hallucinated fake IDs like `"udaipur_2026_luxury_gems"`. Fixed with `InjectedState("trip_id")`.
- Migration 005 must be run manually on Supabase (`ALTER TABLE trips ADD COLUMN board_items JSONB DEFAULT '[]'`)

### Known issues (Phase 4)
- Cards lack clickable affiliate links (see Phase 4 diagnosis)
- Agent sometimes hallucates data instead of calling `booking_search`
- No activity or flight search tools

---

## Phase 4: Real Data & Links — IN PROGRESS

**Goal:** Cards on the board have real, up-to-date data with clickable affiliate links. Agent always uses search tools.

### Diagnosis

Testing revealed 4 issues with the current board cards:

**1. No clickable links on cards**

The pipeline *supports* links end-to-end:
- `booking_search` → returns `Hotel` objects with `affiliate_url`
- `generate_card_elements` → reads `bookingUrl` from item data
- `create_card_group` → sets `link=booking_url` on the Excalidraw rectangle

But the break is in the middle: `booking_search` returns **formatted text** with URLs buried in prose. The LLM then calls `board_add_items` with a JSON string it constructs itself — and **drops the URLs** during that translation.

**Root cause:** The agent reads text like `"Book: https://long-affiliate-url..."` and must manually extract it into structured JSON. LLMs reliably copy names/prices but often hallucinate or omit long URLs.

**2. No up-to-date data on cards**

The agent sometimes skips `booking_search` entirely and uses training data to generate hotel names, prices, and ratings. The system prompt says "use search tools" but doesn't enforce it.

**3. No activities**

No activity search skill exists. When users ask for activities, the agent either:
- Uses `web_search` (returns article links, not booking URLs)
- Hallucates activity data from training knowledge

**4. No flights**

No flight search skill exists at all.

### Plan

| # | Issue | What to do |
|---|-------|------------|
| #11 | booking_search: return structured JSON | Return a JSON array of hotel objects (not formatted text). Agent can pass directly to board_add_items without lossy text→JSON conversion. URLs preserved. |
| #12 | System prompt: enforce tool usage + board schema | Tell agent: (1) ALWAYS use booking_search, never make up hotels, (2) exact JSON schema for board_add_items with bookingUrl field, (3) pass search results directly to board tools |
| #13 | System prompt: enforce tool usage + board schema | Tell agent: (1) ALWAYS use search tools, never make up data, (2) exact JSON schema for board_add_items with bookingUrl field, (3) pass search results directly to board tools, (4) use web_search for activities/flights when no dedicated tool exists |

Issues #11 and #12 are the critical fixes. #13 improves activity/flight coverage using existing tools.

**Approach for activities & flights:** We already have `web_search` (Tavily) and Playwright. The agent should use these to find real data:
- **Activities:** `web_search` for activities at the destination, extract names/prices/URLs from results
- **Flights:** Skyscanner via Playwright (same pattern as Booking.com scraper) — Future Phase skill

### Verify
- [ ] "Find hotels in Lisbon" → agent calls `booking_search` (not hallucinated)
- [ ] "Add the top 3 to the board" → cards have clickable affiliate links
- [ ] Click a card → opens real Booking.com page with affiliate tracking
- [ ] "What activities can I do?" → agent uses web_search, returns real results with links
- [ ] Activity cards have links to source pages
- [ ] Agent never places cards with made-up data

---

## Phase 5: End-to-End Polish

**Goal:** Full flow works smoothly. Edge cases handled.

### Integration Testing
- Full chat → search → add to board → iterate flow
- Multiple trips / boards
- Dashboard thumbnails work with new board structure
- Canvas auto-save still works after agent modifications
- Image hydration works for hotel images

### Edge Cases
- Agent adds items when board is empty (no existing elements)
- Agent adds items when board has user-drawn content
- Very long conversations (message history loading)
- Playwright timeout / Booking.com blocks
- Empty search results

### Polish
- Status messages during long operations ("Searching Booking.com...")
- Error handling in board tools (graceful failures)

### Verify
- [ ] Create new board → chat → search → add to board → see cards → iterate → all works
- [ ] Dashboard shows boards with thumbnails
- [ ] Affiliate links are correct CJ deep links
- [ ] Canvas persists across page reloads
- [ ] Multiple boards are independent

---

## Future Phases (post-MVP)

- **Flight skill** — Skyscanner via Playwright (same pattern as Booking.com scraper)
- **Board reconciliation** — detect when user deletes agent-placed cards
- **Proper auth** — replace X-User-ID with JWT
- **Production deploy** — Railway/Vercel
- **External agent API** — Phase 2 of the big vision (skills as public API)
