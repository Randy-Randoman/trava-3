# Plan: trava-3 Implementation

## Vision

Travel planning platform powered by AI agents. User chats with the agent, agent searches real providers (Booking.com, web), places results as interactive cards on an Excalidraw canvas. Hotel cards link straight to the Booking.com page with dates pre-filled. A personal showcase project, self-hosted.

**MVP:** Chat → search Booking.com → real hotels with booking links → add to board as cards → iterate (add more, remove, replace) → user books via card links.

---

## Key Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| **Agent** | LangGraph ReAct | LLM-agnostic, composable, simple loop |
| **LLM** | Swappable: Gemini (default) or Claude Sonnet 5.5 | Both via langchain, env var config |
| **Skills** | Python packages in `backend/skills/`, auto-discovered | Easy to add, signals future independence |
| **Board** | Incremental (append/remove, not full replace) | Fixes trava-2's core problem |
| **Board state** | `board_items` JSONB on trips table | Agent can read what's on the board |
| **Hotel search** | Playwright + Booking.com | Real results, real links |
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
| [#14] `POST /feedback` endpoint wired up in `main.py` — frontend modal → backend → DB | ✅ *(removed in Phase 10)* |
| Session params stripped from scraped hotel URLs (compared with working skills-try-out repo — `aid`/`sid`/`label` params are Playwright-session-bound and break outside it) | ✅ |
| Booking params (checkin/checkout/adults/rooms) appended to clean hotel URL before CJ wrapping (ported from skills-try-out `add_booking_params` pattern) | ✅ *(CJ wrapping removed in Phase 10)* |

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
- [x] Feedback modal submits successfully from dashboard *(removed in Phase 10)*

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
| `tests/unit/test_deeplink.py` — 6 tests for CJ affiliate link generation (with/without credentials, URL encoding) | ✅ *(removed in Phase 10)* |
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

## Phase 7: Sign-Up Flow ✅

**Goal:** Users can sign up, confirm email, and wait for manual approval before accessing the app.

**Flow:** Sign Up → Email Confirmation → Auth Callback → Pending Approval → Dashboard

### Done

| # | Task | Details | Status |
|---|------|---------|--------|
| 1 | Install `@supabase/ssr`, create server client | `frontend/src/lib/supabase/server.ts` — cookie-based server client | ✅ *(removed in Phase 10)* |
| 2 | Add `signUp` to AuthContext | `signUp(email, password, fullName)` with `full_name` in `options.data` | ✅ |
| 3 | `/signup` page | Form: Full Name, Email, Password. Brutalist styling. Success: "Check your email" message | ✅ |
| 4 | Cross-links login ↔ signup | Both pages link to each other | ✅ |
| 5 | `/auth/callback` route | Exchanges code for session, redirects to `/dashboard` or `/login` | ✅ *(removed in Phase 10)* |
| 6 | Migration 007: `is_approved` | `backend/migrations/007_user_approval.sql` — **user must run in Supabase SQL Editor** | ✅ (code written) *(removed in Phase 10)* |
| 7 | `/pending-approval` page | "Account Under Review" + "Check again" + "Sign out" buttons | ✅ *(removed in Phase 10)* |
| 8 | Approval check in ProtectedRoute | Fetches `is_approved` from profiles, redirects to `/pending-approval` if false | ✅ *(removed in Phase 10)* |

### Bugs fixed during Phase 7

| What was done | Status |
|---------------|--------|
| Duplicate email signup detection: Supabase returns fake success for existing emails — now checks `identities` array and shows "account already exists" error | ✅ |
| ProtectedRoute approval check: was letting users through when profile row didn't exist (`undefined !== false`). Fixed to require explicit `is_approved === true` | ✅ |

### Issues
- [#29](https://github.com/Randy-Randoman/trava-3/issues/29) — Sign-up page and AuthContext signUp method (tasks 2-4)
- [#30](https://github.com/Randy-Randoman/trava-3/issues/30) — Auth callback route with Supabase SSR (tasks 1, 5)
- [#31](https://github.com/Randy-Randoman/trava-3/issues/31) — User approval gate: migration, pending page, ProtectedRoute check (tasks 6-8)

### Manual steps (user must do — agent cannot)
These steps require access to the Supabase dashboard or a real browser. The agent writes the code, but these must be done by the user before testing.

1. **Run migration 007** in Supabase SQL Editor — file is at `backend/migrations/007_user_approval.sql`. Copy-paste and run it.
2. **Configure Resend as SMTP provider** — Supabase dashboard → Authentication → Settings → SMTP. Enable "Custom SMTP" and enter Resend SMTP credentials (host: `smtp.resend.com`, port: 465, user: `resend`, pass: your Resend API key). This makes confirmation emails go through Resend instead of Supabase's built-in (rate-limited) sender.
3. **Enable email confirmations** — Supabase dashboard → Authentication → Settings → Email. Make sure "Enable email confirmations" is ON so users must verify their email before accessing the app.
4. **Check Supabase redirect URL** — Supabase dashboard → Authentication → URL Configuration. The "Site URL" should be `http://localhost:3000` and "Redirect URLs" should include `http://localhost:3000/auth/callback`. Without this, the email confirmation link won't work. *(removed in Phase 10)*
5. **Test the full flow** — sign up with a real email, confirm via Resend email, see pending-approval page, manually approve in DB (`UPDATE profiles SET is_approved = true WHERE id = '...';`), refresh, access dashboard. *(removed in Phase 10)*
6. **Approve existing users** — any users who signed up before migration 007 will have `is_approved = false` and get locked out. Run: `UPDATE profiles SET is_approved = true;` to approve all existing users. *(removed in Phase 10)*

### Not in this phase
- Backend JWT validation (see Phase 8)

---

## Phase 8: Share & Feedback UX ✅

**Goal:** Users can share their trip board with others and give feedback from inside the trip planner.

### Done

| # | Task | Details | Status |
|---|------|---------|--------|
| 1 | [#33] Share button on trip canvas | `ShareButton` component: flushes canvas, calls `POST /trips/{trip_id}/share`, copies share link to clipboard with "Copied!" confirmation | ✅ |
| 2 | [#34] Shared board: no agent | `/board/[share_token]` is view-only, no chat panel or agent. Just the canvas with clickable affiliate links | ✅ *(affiliate links removed in Phase 10)* |
| 3 | [#35] Feedback button on trip canvas | `FeedbackModal` extracted to shared component, Feedback button added to ChatInterface header | ✅ *(removed in Phase 10)* |

### Bugs fixed during Phase 8

| What was done | Status |
|---------------|--------|
| Public board blank canvas: `halftone-overlay` (fixed full-screen div at z-index 0) was covering Excalidraw's rendering layer. Fixed with `relative z-10` on board page container. | ✅ |
| Extracted `FeedbackModal` from dashboard into shared `components/FeedbackModal.tsx` for reuse | ✅ *(removed in Phase 10)* |

### Tests added
- `tests/unit/test_share.py` — 6 tests for share endpoints (token generation, reuse, public board data, 404s)
- All 48 tests passing

### Issues
- [#33](https://github.com/Randy-Randoman/trava-3/issues/33) — Share button on trip canvas
- [#34](https://github.com/Randy-Randoman/trava-3/issues/34) — Shared board: view-only, no agent
- [#35](https://github.com/Randy-Randoman/trava-3/issues/35) — Feedback button on trip canvas

---

## Phase 9: Full Auth Security Pass ✅

**Goal:** Replace `X-User-ID` header with proper Supabase JWT validation + add trip ownership checks to all endpoints. Backend verifies the user's identity instead of trusting a header. No endpoint exposes another user's data.

### Done

| # | Task | Details | Status |
|---|------|---------|--------|
| 1 | JWT auth dependency | `backend/app/core/auth.py` — `require_auth` FastAPI dependency, JWKS (ES256) with cached keys, audience validation | ✅ |
| 2 | Trip ownership helper | `verify_trip_owner(trip_id, user_id)` — 404 if not found, 403 if wrong user, returns trip dict | ✅ |
| 3 | Protect user-scoped endpoints | `Depends(require_auth)` on: `POST /trips`, `GET /trips`, `GET /trips/latest/id`, `POST /feedback` | ✅ *(`/feedback` removed in Phase 10)* |
| 4 | Protect trip-scoped endpoints | Auth + ownership on: canvas GET/PUT, trip GET/PATCH/DELETE, budget, share | ✅ |
| 5 | Protect chat endpoints | Auth + ownership on: `POST /chat/stream`, `GET /chat/messages/{trip_id}` | ✅ |
| 6 | Frontend: Bearer token | `getAuthHeaders()` sends `Authorization: Bearer <access_token>` | ✅ |
| 7 | Frontend: chat auth | Auth headers added to both `useChat.ts` fetches (stream + messages) | ✅ |
| 8 | Cleanup | Removed `DEFAULT_USER_ID`, `AUTH_ENABLED`, `get_user_id()` from config + all backend files | ✅ |

### Tests added
- `tests/unit/test_auth.py` — 13 tests (require_auth, verify_trip_owner, JWKS caching)
- `test_share.py` updated for auth dependency override
- **61 tests total, all passing**

### Bugs fixed during Phase 9
| What was done | Status |
|---------------|--------|
| JWKS URL: Supabase serves JWKS at `/auth/v1/.well-known/jwks.json`, not `/.well-known/jwks.json` | ✅ |
| Trailing slash in `SUPABASE_URL` env var caused double-slash in JWKS URL — fixed with `rstrip("/")` | ✅ |
| JWT audience validation: Supabase tokens include `aud: "authenticated"` — added `audience="authenticated"` to decode | ✅ |

### Endpoints — auth matrix

| Endpoint | Auth | Ownership |
|----------|------|-----------|
| `GET /`, `GET /health` | None | None |
| `GET /trips/public/{share_token}` | None | None |
| `POST /trips`, `GET /trips`, `GET /trips/latest/id` | JWT → user_id | Scoped by user_id |
| `POST /feedback` *(removed in Phase 10)* | JWT → user_id | None (standalone) |
| `GET/PUT /trips/{trip_id}/canvas` | JWT → user_id | verify owner |
| `GET /trips/{trip_id}` | JWT → user_id | verify owner |
| `PATCH/DELETE /trips/{trip_id}` | JWT → user_id | verify owner |
| `GET /trips/{trip_id}/budget` | JWT → user_id | verify owner |
| `POST /trips/{trip_id}/share` | JWT → user_id | verify owner |
| `POST /chat/stream` | JWT → user_id | verify owner (via trip_id in body) |
| `GET /chat/messages/{trip_id}` | JWT → user_id | verify owner |

### Issues
- [#38](https://github.com/Randy-Randoman/trava-3/issues/38) — JWT auth dependency + trip ownership helper (tasks 1-2)
- [#39](https://github.com/Randy-Randoman/trava-3/issues/39) — Protect all backend endpoints (tasks 3-5)
- [#40](https://github.com/Randy-Randoman/trava-3/issues/40) — Frontend: send Bearer token + fix chat auth (tasks 6-7)
- [#41](https://github.com/Randy-Randoman/trava-3/issues/41) — Cleanup: remove legacy auth code (task 8)

---

## Phase 10: Publish-Ready Cleanup ✅

**Goal:** The public repo is safe, accurate and easy to run. It's a personal showcase: people can use it or take inspiration, but it doesn't accept contributions.

### Decisions
| Topic | Decision |
|-------|----------|
| **DB security** | New migration: drop `is_approved`, drop the "anyone can view shared trips/canvas" policies, owner-scoped `canvas-images` write policies |
| **User approval** | Removed entirely (to lock down your own instance, disable sign-ups in Supabase) |
| **Image proxy** | Stays public (shared boards need it); block internal addresses + redirects, `image/*` only without SVG, 5 MB cap, no CORS `*` |
| **Feedback** | Removed entirely (no issues or contributions) |
| **Auth** | One path: browser supabase-js. Delete `/auth/callback` + `@supabase/ssr` |
| **LLM** | Gemini (default) or Claude Sonnet 5.5 (`claude-sonnet-5-5`), `ainvoke` |
| **Dependencies** | next 16.4.x, React 19 types, eslint 9 flat config, `npm audit fix` without force, Excalidraw advisories accepted; backend pinned + `requirements-dev.txt` |
| **Layout** | Skills only in `backend/skills/`; tests in `backend/tests/{unit,integration}`; migrations in `supabase/migrations/` |
| **Tests** | Backend unit + integration (local Supabase via CLI) + frontend unit (Vitest). No E2E, no CI |
| **Deploy** | Docker Compose + your own Railway, documented in `docs/deploy.md`; no Railway template |
| **Git history** | Not rewritten (only the publishable Supabase key leaked, which is public by design) |
| **Delivery** | GitHub issues labelled `ready-for-agent`, worked on `dev`, one PR `dev` → `main` |

### Issues
| # | Issue | Blocked by |
|---|-------|-----------|
| [#42](https://github.com/Randy-Randoman/trava-3/issues/42) | Restructure skills, tests and migrations | — |
| [#43](https://github.com/Randy-Randoman/trava-3/issues/43) | Security migration + remove user approval | #42 |
| [#44](https://github.com/Randy-Randoman/trava-3/issues/44) | Vitest setup + harden image proxy | #42 |
| [#45](https://github.com/Randy-Randoman/trava-3/issues/45) | Remove feedback feature and unused auth callback | #42 |
| [#46](https://github.com/Randy-Randoman/trava-3/issues/46) | Upgrade and pin dependencies, fix lint | #42 |
| [#47](https://github.com/Randy-Randoman/trava-3/issues/47) | Backend hardening (errors, logging, config, async agent) + dead code | #42 |
| [#48](https://github.com/Randy-Randoman/trava-3/issues/48) | Unit tests for board tools and budget parsing | #42 |
| [#49](https://github.com/Randy-Randoman/trava-3/issues/49) | Frontend fixes (SSE buffering, env checks) + cleanup | #44, #46 |
| [#50](https://github.com/Randy-Randoman/trava-3/issues/50) | Integration tests against local Supabase | #42, #43 |
| [#51](https://github.com/Randy-Randoman/trava-3/issues/51) | Docker + Railway deployment for self-hosters | #46 |
| [#52](https://github.com/Randy-Randoman/trava-3/issues/52) | Docs and showcase cleanup | all above |

### Manual steps (user must do — agent cannot)
- Apply the security migration to the live Supabase project (`supabase link` + `supabase db push`, or the SQL editor)
- ~~GitHub: add a description and topics~~ ✅ (Issues stay on for own tracking only)
- ~~Close stale issues #18, #19, #20~~ ✅ closed
- ~~Delete the stale `claude/debug-railway-error-NuJhs` branch and the local `worktree-agent-*` branches~~ ✅ (its CORS-parsing fix moved into #51)

### Backlog (not this phase)
- Store card images in Supabase storage instead of proxying them
- E2E tests (Playwright), CI
- Squash migrations into one schema file

---

## Phase 11: MCP Server (Bring Your Own Agent)

**Goal:** External agents (Claude Code, Claude Cowork, any MCP client) can plan trips on the TRAVA board.

### Decisions
| Topic | Decision |
|-------|----------|
| **Hosting** | Remote Streamable HTTP MCP server at `/mcp`, inside the FastAPI backend (deploys with it) |
| **Auth** | OAuth 2.1 with Supabase Auth as the authorization server (PKCE, dynamic client registration). TRAVA hosts `/oauth/consent` + a "Connected apps" page; the backend verifies agent JWTs (JWKS, `client_id` claim, live grant check) and serves the RFC 9728 metadata. Same pattern as the solofounder-playbook project |
| **Tools** | `list_trips`, `create_trip`, `board_read/add_items/remove_items/clear`, `booking_search`, `web_search`, `image_search`; ownership check on every `trip_id` |
| **Skill reuse** | Skills get plain async functions with explicit `trip_id`; the `@tool` wrappers stay for LangGraph |
| **Live sync** | Supabase Realtime on `canvas_states` → open board reloads |
| **Stale tabs** | Canvas save sends `base_version`; 409 on conflict, so reconciliation never deletes unseen items |
| **Clients** | Claude Code (`claude mcp add --transport http`), Claude Cowork / claude.ai custom connectors (need a public HTTPS URL) |

### Issues
| # | Issue | Blocked by |
|---|-------|-----------|
| [#53](https://github.com/Randy-Randoman/trava-3/issues/53) | Make skills callable without the LangGraph agent | Phase 10 |
| [#54](https://github.com/Randy-Randoman/trava-3/issues/54) | OAuth 2.1 for agents (Supabase Auth, consent page, token verification) | Phase 10 |
| [#55](https://github.com/Randy-Randoman/trava-3/issues/55) | Remote MCP server at `/mcp` | #53, #54 |
| [#56](https://github.com/Randy-Randoman/trava-3/issues/56) | Canvas save conflicts (stale tab must not delete items) | Phase 10 |
| [#57](https://github.com/Randy-Randoman/trava-3/issues/57) | Live board updates via Supabase Realtime | #56 |
| [#58](https://github.com/Randy-Randoman/trava-3/issues/58) | Document MCP usage | #55, #57 |

### Manual steps (user must do — agent cannot)
- Supabase → Authentication → OAuth Server: enable it, authorization path `/oauth/consent`, allow dynamic client registration
- Supabase JWT signing key must be asymmetric (ES256/RS256)
- Set `PUBLIC_BASE_URL` on the backend service (Railway)

---

## Phase 12: Better Board UX

**Goal:** The board is worth planning on — not just a card dump, but a real trip planner.

### Already implemented
- [#18] Day-by-day layout — transformer groups items by `day` field into columns with date headers ✅
- [#19] Budget tracking — floating BudgetPanel, backend `/trips/{trip_id}/budget` endpoint ✅
- [#20] Shareable board links — backend + public route implemented ✅ (UI added in Phase 8)

### Remaining
- Share button: display the share link visually on the board (not just clipboard copy — clipboard fails in some browsers/contexts)
- UI to set/edit trip budget (currently must be set in DB directly)
- Agent budget awareness (skill to read budget status)

---

## Phase 13: Scraping Resilience

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

## Phase 14: End-to-End Polish

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
| 10 | **Feedback endpoint** | ✅ Already done in Phase 4 *(removed in Phase 10)* |

---

## Future Phases (post-MVP)

- **Flight skill** — Skyscanner via Playwright (same pattern as Booking.com scraper)
- **Board reconciliation** — detect when user deletes agent-placed cards, sync board_items
- **Social login** — Google, Apple
- **Production deploy** — Railway / Vercel
- **External agent API** — skills as public API (Phase 2 of the big vision)

---

## Learnings

