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

## Phase 2: Skills + Agent — IN PROGRESS

**Goal:** Agent can chat and call tools. Skills are loaded from the registry.

**Tracked in GitHub Issues:** https://github.com/Randy-Randoman/trava-3/issues

| # | Issue | Description | Depends on |
|---|-------|-------------|------------|
| #1 | LangGraph agent: state, graph, system prompt | Agent core — ReAct graph, swappable LLM, dynamic prompt | — |
| #2 | Chat endpoint: SSE streaming with LangGraph | Rewrite chat.py stub for real streaming | #1 |
| #3 | Playwright service: shared headless browser | Singleton browser manager for Booking.com scraping | — |
| #4 | Booking skill: search + CJ affiliate links | Playwright scraping, deeplink generation, @tool wrappers | #3 |
| #5 | Web search skill: Tavily integration | Web + image search @tools | — |
| #6 | Board skill: stub tool implementations | Placeholder tools + BoardItem model for Phase 3 | — |

### Verify
- [ ] Chat with agent — get a response
- [ ] "Find hotels in Lisbon" → agent calls booking_search → returns results with affiliate links
- [ ] "Search for things to do in Lisbon" → agent calls web_search → returns info
- [ ] SSE streaming works (status updates, text chunks)

---

## Phase 3: Board Intelligence

**Goal:** Agent can read, add to, remove from, and clear the board. Canvas updates incrementally.

### Database
- `migrations/005_board_items.sql` — add board_items JSONB column to trips

### Transformer
- `backend/app/logic/transformer.py` — add `generate_card_elements()`:
  - Takes items + existing_elements
  - Finds max_y of existing content
  - Places new cards below using masonry layout
  - Returns new_elements, new_files, group_ids (to append, not replace)

### Board Tools (wire to canvas)
- `skills/board/tools.py`:
  - `board_read` — reads board_items from trip, returns formatted summary
  - `board_add_items` — generates card elements, appends to canvas, updates board_items
  - `board_remove_items` — filters elements by groupId, removes from canvas + board_items
  - `board_clear` — removes all agent-placed groups, preserves user content

### Database Service
- `backend/app/services/database.py` — add board_items read/write methods

### SSE Integration
- Board tools emit `canvas_updated` SSE event after updating canvas
- Frontend useChat.ts handles `canvas_updated` → dispatches window event → BoardWrapper reloads

### Verify
- [ ] "Find hotels in Lisbon" → agent responds with results
- [ ] "Add the top 3 to the board" → 3 hotel cards appear on canvas
- [ ] Cards have clickable affiliate links
- [ ] "What's on my board?" → agent lists the 3 hotels
- [ ] "Remove the first one" → card removed, canvas updates
- [ ] User draws on canvas → agent additions don't erase user content
- [ ] Multiple add rounds → cards stack below previous ones

---

## Phase 4: End-to-End Polish

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
- Agent prompt tuning (when to search, when to add to board, how to present results)

### Verify
- [ ] Create new board → chat → search → add to board → see cards → iterate → all works
- [ ] Dashboard shows boards with thumbnails
- [ ] Affiliate links are correct CJ deep links
- [ ] Canvas persists across page reloads
- [ ] Multiple boards are independent

---

## Future Phases (post-MVP)

- **Itinerary skill** — research destinations, suggest day plans
- **Flight skill** — search flights (Amadeus or similar)
- **Activities skill** — GetYourGuide or similar
- **Board reconciliation** — detect when user deletes agent-placed cards
- **Proper auth** — replace X-User-ID with JWT
- **Production deploy** — Railway/Vercel
- **External agent API** — Phase 2 of the big vision (skills as public API)
