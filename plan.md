# Plan: trava-3 Implementation

## Vision

Travel planning platform powered by AI agents. User chats with the agent, agent searches real providers (Booking.com, web), places results as interactive cards on an Excalidraw canvas. Every hotel card carries an affiliate link — we earn commission on bookings.

**MVP:** Chat → search Booking.com → real hotels with affiliate links → add to board as cards → iterate (add more, remove, replace) → user books via card links.

---

## Key Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| **Agent** | LangGraph ReAct | LLM-agnostic, composable, simple loop |
| **LLM** | Swappable (Gemini default, Anthropic optional) | Both via langchain, env var config |
| **Skills** | Python packages at root `skills/`, auto-discovered | Easy to add, signals future independence |
| **Board** | Incremental (append/remove, not full replace) | Fixes trava-2's core problem |
| **Board state** | `board_items` JSONB on trips table | Agent can read what's on the board |
| **Hotel search** | Playwright + Booking.com | Real results, real links |
| **Affiliate** | CJ deep links | Revenue on every booking |
| **Tool → board data** | Tools return structured JSON, not text | LLMs drop URLs when converting text→JSON |
| **Tool state injection** | `InjectedState("trip_id")` | LLMs hallucinate IDs if given as a normal param |

---

## Phase 1: Scaffold ✅

Copied trava-2 frontend + backend, adapted for new architecture. App shell runs.

## Phase 2: Skills + Agent ✅

LangGraph agent, 8 tools auto-discovered, SSE streaming chat, Playwright singleton.

## Phase 3: Board Intelligence ✅

Board tools wired to canvas (read/add/remove/clear), incremental masonry layout, `canvas_updated` SSE events, `InjectedState` for trip_id.

<details>
<summary>Phase 1-3 details (click to expand)</summary>

### Phase 1: Scaffold + Copy

**Completed 2025-02-23.**

- Frontend: 33 files from trava-2, `useChat.ts` adapted for `canvas_updated`
- Backend: FastAPI shell, trips CRUD, canvas CRUD, chat stub (501)
- Skills registry with 3 stubs (booking, board, web_search)
- Migration 005: `board_items` JSONB column

Fixes: missing `public/` dir, mirrored logo, over-zoomed board, dashboard scroll, auth token handling.

### Phase 2: Skills + Agent

**Completed 2026-02-24. Issues #1-#6.**

- Agent: ReAct graph, swappable LLM (Gemini/Anthropic), dynamic system prompt
- Chat: SSE streaming (`status`/`text`/`canvas_updated`/`done`/`error`), message persistence
- Skills: `booking_search`, `deeplink_generate`, `web_search`, `image_search`, 4 board stubs
- Playwright singleton with graceful shutdown

Fixes: lazy imports for skills, Gemini content block format, model upgrade to `gemini-3-flash-preview`.

### Phase 3: Board Intelligence

**Completed 2026-02-24. Issues #7-#10.**

- DB: `get_board_items()` / `update_board_items()` on DatabaseService
- Transformer: `generate_card_elements()` — masonry layout below existing content
- Board tools: real implementations for read/add/remove/clear
- SSE: `canvas_updated` event after board-mutating tools

Fixes: `InjectedState("trip_id")` — LLM was hallucinating fake trip IDs like `"udaipur_2026_luxury_gems"`.

</details>

---

## Phase 4: Real Data & Links ✅

**Goal:** Cards have real data, clickable links, images, and descriptions. Agent always uses search tools.

### Done

| What was done | Status |
|---------------|--------|
| `booking_search` returns structured JSON (not formatted text) — agent passes directly to `board_add_items`, URLs preserved | ✅ |
| System prompt enforces tool usage, provides `board_add_items` JSON schema with `bookingUrl` field, guides `web_search` for activities/flights | ✅ |
| [#11] Image pipeline fixed: `search_tavily_image` converted to async (was blocking event loop), Booking.com scraper now tries `data-src`/`srcset` for lazy-loaded images | ✅ |
| [#12] `description` field flows through entire pipeline: `booking_search` → `generate_card_elements` → `create_card_group`. Prompt schema updated. | ✅ |
| [#13] System prompt + web_search skill prompt guide agent to search Skyscanner/Google Flights/Kayak directly for flight bookingUrls | ✅ |
| [#14] `POST /feedback` endpoint wired up in `main.py` — frontend modal → backend → DB | ✅ |
| Session params stripped from scraped hotel URLs (compared with working skills-try-out repo — `aid`/`sid`/`label` params are Playwright-session-bound and break outside it) | ✅ |
| Booking params (checkin/checkout/adults/rooms) appended to clean hotel URL before CJ wrapping (ported from skills-try-out `add_booking_params` pattern) | ✅ |

### Known issues (moved to Phase 5)

- Only 1 hotel returned (scraper/pipeline bug)
- Closed/delisted hotels still appear
- No way to test skills in isolation

### Verify
- [ ] Hotel cards show real photos (not broken image icons)
- [ ] Cards have descriptions of what to expect
- [ ] Hotel cards have clickable links → opens Booking.com hotel page with dates pre-filled
- [ ] Search returns 5-10 hotels (not just 1)
- [ ] Activity cards have links to source pages
- [ ] Flight cards link to booking sites (not blog posts)
- [ ] Agent always uses search tools, never hallucinates data
- [x] Feedback modal submits successfully from dashboard

---

## Phase 5: Skill Testing & Scraping Fixes ✅

**Goal:** Skills can be tested in isolation without running the full app. Scraping returns reliable results.

### Done

| What was done | Status |
|---------------|--------|
| Slow dashboard load fixed: Next.js middleware redirects `/` → `/dashboard` before Excalidraw bundle loads | ✅ |
| Playwright browser warms up in background on backend startup (ready by the time user chats) | ✅ |
| [#16] Fix "only 1 hotel" bug: root cause was `"searchresults" in raw_url` matching `&from=searchresults` query param on every valid hotel URL. Fixed to check URL path only. Now returns 10 hotels. | ✅ |
| [#17] Scraping resilience: `quote()` for destination in search URL, skip hotels with no valid URL, detailed logging (URL found, cards count, skipped count), `exc_info=True` on errors | ✅ |
| English locale: added `&lang=en-us` to search URL so ratings/distances are in English | ✅ |
| Booking links work end-to-end | ✅ |

### Known issues

- ~~**Skill testing UX.** Need a better way to test skills — possibly via Claude Code integration or a simpler workflow.~~ → Resolved: unit tests added (see below).

### Unit Tests Added

| What was done | Status |
|---------------|--------|
| Extracted `build_search_url()`, `clean_hotel_url()`, `append_booking_params()` from `search.py` into standalone pure functions | ✅ |
| `tests/unit/test_deeplink.py` — 6 tests for CJ affiliate link generation (with/without credentials, URL encoding) | ✅ |
| `tests/unit/test_models.py` — 7 tests for SearchParams/Hotel Pydantic models (defaults, validation, edge cases) | ✅ |
| `tests/unit/test_url_builder.py` — 16 tests for Booking.com search URL construction (filters, sort, encoding, case insensitivity) | ✅ |
| `tests/unit/test_url_cleaning.py` — 13 tests for URL cleaning + booking param appending (searchresults bug regression, session param stripping) | ✅ |
| `pytest.ini` + `tests/conftest.py` with shared fixtures and dummy env vars | ✅ |
| pytest + pytest-asyncio added to `requirements.txt` | ✅ |
| **42 tests, all passing in ~0.2s** | ✅ |

### Bugs fixed after initial Phase 5

| What was done | Status |
|---------------|--------|
| Removed deprecated middleware (Next.js 16 renamed it to "proxy") — was causing "cannot find module" errors. Client-side redirect in page.tsx handles `/` → `/dashboard` instead. | ✅ |
| Excalidraw lazy load: `<BoardWrapper>` only mounts when tripId exists. No Excalidraw bundle on welcome screen or dashboard. | ✅ |
| Trips created with title "New Trip" and status "active" (was "Start New Trip Board" / "draft") | ✅ |

---

## Phase 6: Smarter Agent ✅

**Goal:** Agent is a real travel planner, not just a search wrapper. It builds coherent trips, suggests proactively, and helps with logistics.

### Done

| What was done | Status |
|---------------|--------|
| System prompt rewritten: travel planner personality, day-by-day thinking, proactive suggestions, logistics advice, concise responses | ✅ |

### Verify (live testing)
- [ ] Agent structures trips by day when asked to plan multi-day trips
- [ ] Agent proactively suggests activities after hotel search
- [ ] Agent gives practical logistics advice (transport, weather)
- [ ] Agent stays concise — cards on board are the main output, not text walls
- [ ] Agent still uses tools correctly (no hallucinated data)

### Future (if prompt alone isn't enough)
- `board_add_items` with `day` or `group` field → visual grouping on canvas
- `itinerary_search` tool that wraps web_search with day-plan structure

---

## Phase 7: Better Board UX — NEXT

**Goal:** The board is worth planning on — not just a card dump, but a real trip planner.

### To do

#### [#18] Day-by-day layout
- Cards grouped by day on the canvas (Day 1 column, Day 2 column, etc.)
- Agent or transformer places cards in day groups
- User can drag cards between days

#### [#19] Budget tracking
- Board shows running total of all card prices
- Could be a special "budget" element on the canvas, or a sidebar widget
- Agent can answer "what's my total so far?" by reading board_items and summing prices

#### [#20] Shareable board links
- `share_token` column already exists on trips
- Build a public read-only view: `/board/:share_token`
- No auth required — anyone with the link can see the board
- Affiliate links still work on shared boards (revenue from shares!)

---

## Phase 8: Scraping Resilience

**Goal:** Booking.com scraping doesn't break silently. Failures are detected, logged, and handled.

### Monitoring
- Health check endpoint that runs a test search: `GET /health/booking`
- Returns last successful scrape time, error count, avg response time

### Fallback chain
- If Playwright scraping fails: try 2 retries with different User-Agent
- If still fails: fall back to `web_search` for hotels (lower quality but not broken)
- Agent gets a clear message: "Live search is unavailable, using web results instead"

### Error handling
- Playwright timeout → return partial results if any, or clear error
- Booking.com CAPTCHA/block → detect and report, don't hang
- Rate limiting — don't hammer Booking.com (add delays between searches)

---

## Phase 9: End-to-End Polish

**Goal:** Full flow works reliably. Edge cases handled. Ready for demo.

| # | Area | What to verify / fix |
|---|------|---------------------|
| 1 | **Full flow** | Create board → chat → search → add to board → see cards → iterate → remove → all works |
| 2 | **Multiple boards** | Each trip has independent board_items, canvas, conversation |
| 3 | **Dashboard** | Thumbnails show card images from canvas state |
| 4 | **Canvas persistence** | Auto-save works after agent modifications, survives page reload |
| 5 | **Empty board** | Agent adds items when board has no existing elements |
| 6 | **User content** | Agent additions don't erase user-drawn content (freehand, text, etc.) |
| 7 | **Long conversations** | Message history loading works with 50+ messages |
| 8 | **Empty search results** | "No hotels found" → agent tells user, doesn't add empty cards |
| 9 | **Status messages** | "Searching Booking.com..." / "Adding to board..." shown during long operations |
| 10 | **Feedback endpoint** | ✅ Already done in Phase 4 |

---

## Future Phases (post-MVP)

- **Flight skill** — Skyscanner via Playwright (same pattern as Booking.com scraper)
- **Board reconciliation** — detect when user deletes agent-placed cards, sync board_items
- **Proper auth** — replace X-User-ID header with JWT
- **Production deploy** — Railway / Vercel
- **External agent API** — skills as public API (Phase 2 of the big vision)

---

## Learnings

