# Learnings from trava-2/Untitled

What worked, what didn't, and what to carry forward into trava-3.

---

## What trava-2 IS

A working travel planning app: chat with an AI agent (Gemini), it searches flights/hotels/activities, then generates an Excalidraw board with visual cards. Split-screen UI — 35% chat, 65% canvas. Supabase for auth + persistence. Brutalist design system.

**It works end-to-end.** User chats → agent searches → board appears on canvas.

---

## Architecture Overview

```
Frontend (Next.js 16 + React 19 + Tailwind)
    ↓ POST /chat/stream (SSE)
Backend (FastAPI)
    ↓ Gemini tool-calling loop
Agent (custom state machine in agent.py)
    ↓ Tools: search_flights, search_hotels, search_images, search_destination_info
Services (Amadeus, Tavily, Supabase)
    ↓
Transformer (agent JSON → Excalidraw elements)
    ↓ PUT /trips/{id}/canvas
Excalidraw (embedded React component)
```

---

## What Works Well (REUSE)

### 1. Frontend — Copy as-is

| Component | What it does | Notes |
|-----------|-------------|-------|
| `BoardWrapper.tsx` | Excalidraw embed, auto-save (2s debounce), canvas-updated event listener | Rock solid. Dynamic import avoids SSR issues. |
| `useExcalidrawHydration.ts` | Converts image URLs → base64 via proxy, keeps URLs in DB | Clever two-layer system. Critical for images on canvas. |
| `ChatInterface.tsx` | Chat container with messages, thinking indicator, status toasts | Works well. SSE event handling is clean. |
| `ChatBubble.tsx` | ReactMarkdown message renderer with timestamps | Simple, works. |
| `InputArea.tsx` | Auto-expanding textarea, Shift+Enter for multiline | Good UX. |
| `ThinkingIndicator.tsx` | Bouncing dots animation | Simple. |
| `StatusToast.tsx` | Shows "Searching flights..." type status updates | Nice touch for long operations. |
| `AuthContext.tsx` + `ProtectedRoute.tsx` | Supabase auth wrapper | Works but auth is currently disabled (AUTH_ENABLED=false). |
| `api.ts` | Backend fetch helpers | Clean. Needs minor endpoint adjustments. |
| `useChat.ts` | SSE streaming hook, board_data handling, message state | **Core integration point.** Handles the full flow: send message → stream response → trigger canvas update. |
| `dashboard/page.tsx` | Trip grid with thumbnails, rename, delete | Works. Uses first canvas image as thumbnail. |
| `page.tsx` (home) | 35/65 split layout, welcome screen, trip creation | Works. |
| `login/page.tsx` | Email/password auth form | Brutalist styled. |
| `image-proxy/route.ts` | CORS proxy for external images | Required for Excalidraw image loading. |
| `tailwind.config.js` | Brutalist design system | Distinctive look. retro-cream, trava-teal, adventure-orange, shadow-brutal. |

### 2. Backend — Copy as-is

| File | What it does | Notes |
|------|-------------|-------|
| `database.py` | Full Supabase wrapper (trips, canvas, conversations, messages CRUD) | Well-structured. Uses service key to bypass RLS (MVP approach). |
| `transformer.py` | Trip JSON → Excalidraw elements. Masonry layout, color-coded cards. | **Critical.** This is the visual magic. 3-column grid, image cards with booking links. |
| `trips.py` | All trip CRUD + canvas + transform endpoints | Complete. The `/trips/transform` endpoint is the bridge between agent and canvas. |
| `config.py` | Pydantic settings | Adapt env var names. |
| `templates.py` | Welcome canvas template | Nice onboarding touch — shows a starter canvas when trip is created. |
| Migrations 001-004 | profiles, trips, canvas_states, conversations, messages + RLS | Solid schema. Cascade deletes work. |

### 3. Backend — Copy + Adapt

| File | Changes needed |
|------|---------------|
| `chat.py` | Rewrite SSE streaming to use LangGraph instead of custom Gemini loop. Keep same SSE event format (status, text, board_data, done, error) so frontend works unchanged. |
| `prompts.py` | New system prompt for Claude. Keep BOARD_JSON_SCHEMA as-is — it's the contract between agent and transformer. |

### 4. Backend — Don't Copy (rewrite)

| File | Why |
|------|-----|
| `agent.py` | Custom Gemini tool loop with state tracking. Replace with LangGraph graph. |
| `llm.py` | Google Generative AI SDK. Replace with langchain LLM. |
| `amadeus.py` | Flight/hotel search. Not needed for MVP (booking skill replaces this). |
| `tavily.py` | Rewrite as a skill or built-in tool. |

---

## Key Integration Contracts (DO NOT BREAK)

### 1. SSE Event Format (frontend ↔ backend)
```
event: status    → { content: "Searching hotels..." }
event: text      → { content: "Here are 5 hotels in Lisbon..." }
event: board_data → { content: { trip: {...}, stays: [...], activities: [...] } }
event: done      → { content: "" }
event: error     → { content: "Something went wrong" }
```
Frontend useChat.ts parses these. Keep this format and the frontend works unchanged.

### 2. Board Data JSON Schema (agent → transformer)
```json
{
  "trip": { "destination", "startDate", "endDate", "budget", "currency", "travelers", "vibe" },
  "flights": [{ "id", "name", "origin", "destination", "price", "bookingUrl", "imageUrl", ... }],
  "stays": [{ "id", "name", "location", "checkIn", "checkOut", "price", "bookingUrl", "imageUrl", ... }],
  "activities": [{ "id", "name", "description", "price", "bookingUrl", "imageUrl", ... }]
}
```
This is the contract between the agent and the transformer. The transformer reads this and creates Excalidraw elements. Keep this format and the canvas generation works unchanged.

### 3. Canvas State Format (backend ↔ Excalidraw)
```json
{
  "elements": [...],     // Excalidraw element objects
  "files": {             // Image files keyed by fileId
    "fileId": {
      "mimeType": "image/jpeg",
      "dataURL": "https://...",  // External URL (not base64!)
      "created": timestamp
    }
  },
  "appState": {...}      // Excalidraw app state
}
```
Backend stores URLs in files. Frontend hydration hook converts to base64 in memory. Don't change this.

### 4. Canvas Update Event Flow
```
Agent generates board_data
  → SSE sends board_data event to frontend
  → Frontend calls POST /trips/transform { trip_id, board_data }
  → Backend runs transformer, saves to canvas_states
  → Frontend dispatches window event 'canvas-updated'
  → BoardWrapper listens, reloads canvas from DB
```

---

## What Didn't Work Well

### 0. Core UX Problems (most important)

**Boards were not reusable / not iterative.**
The transformer does a full canvas replace every time. When the agent "creates a board," it wipes everything and starts fresh. Users can't say "add a restaurant near that hotel" or "swap out hotel #2" — every board_data event replaces the entire canvas. This kills the iterative planning experience. Excalidraw is powerful because you can build up a visual plan over time, but trava-2 treats it as a one-shot render.

**Agent is blind to the board.**
The agent has no way to read what's currently on the canvas. It can't reference existing elements, remove specific cards, or place new ones relative to what's already there. The flow is one-directional: agent → canvas. There's no canvas → agent feedback loop. So the agent can't answer "what hotels do I have on the board?" or "replace the second hotel with something cheaper."

**Recommendations and links were poor quality.**
Amadeus API results were generic — no real prices, vague hotel names, no ratings or reviews. The booking links were just search URLs (Google Flights, Booking.com search page), not deep links to specific hotels. Users couldn't click and actually book. This undermines the whole monetization model. Switching to Playwright + Booking.com scraping should fix this — real results with real prices, ratings, review counts, and specific hotel pages we can wrap in affiliate links.

### 1. Agent Architecture (agent.py)
- **Tightly coupled to Gemini SDK.** FunctionDeclaration, function_response parts, Gemini-specific content types. Can't swap LLMs without rewriting everything.
- **"Create board" detection is fragile.** Uses `if "create board" in user_message.lower()` — breaks with any phrasing variation.
- **State tracking is manual.** Tracks 5 fields (destination, dates, budget, travelers, vibe) in agent state. Better to let the LLM handle this naturally.
- **Retry logic for board JSON.** Has a 2x retry loop for JSON extraction from Gemini output. Structured output / tool calling is more reliable.

### 2. Tool System
- **Tools defined as Gemini FunctionDeclarations** in llm.py. Not portable.
- **Tool execution is a big if/elif chain** in agent._execute_function. Not extensible.
- **No skill abstraction.** Adding a new tool means editing 3 files (llm.py declarations, agent.py execution, services/*.py implementation).

### 3. Auth
- **Disabled in production.** AUTH_ENABLED=false. Uses DEFAULT_USER_ID.
- **Service key bypasses RLS.** Works for MVP but not secure.

### 4. Hardcoded Values
- DEFAULT_USER_ID throughout
- Welcome template is static
- Layout constants (1248px viewport, 3 columns) not configurable
- 300s timeout, no circuit breakers

---

## What Changes in trava-3

| trava-2 | trava-3 | Why |
|---------|---------|-----|
| Gemini (google-generativeai) | Claude via langchain-anthropic (swappable) | LLM-agnostic via LangGraph |
| Custom tool loop in agent.py | LangGraph StateGraph (ReAct) | Standard pattern, composable |
| FunctionDeclaration (Gemini SDK) | @tool decorators (LangChain) | Framework-agnostic tool definitions |
| if/elif tool dispatch | Skills directory with auto-discovery | Extensible — new skill = new folder |
| Amadeus flights/hotels | Booking.com via Playwright + CJ affiliate links | Different monetization model |
| "create board" string match | Agent decides when to create board via tool | More natural, tool-based |
| search_images (Tavily only) | Keep Tavily, add more sources later | Skills system makes this easy |

---

## The Board JSON Schema Question

The current BOARD_JSON_SCHEMA has `flights`, `stays`, `activities`. For trava-3 MVP we only have `stays` (from booking skill). Options:

1. **Keep the full schema** — flights and activities arrays will just be empty. Transformer handles this fine.
2. **Simplify for MVP** — only `trip` + `stays`. Add back flights/activities when those skills exist.

**Recommendation:** Keep the full schema. The transformer already handles empty arrays. Less refactoring later.

---

## Key Numbers

- **Frontend:** ~15 source files to copy
- **Backend:** ~10 source files to copy, ~4 to rewrite
- **New code:** Skills system + LangGraph agent + Playwright service + booking skill
- **Database:** Same schema, same migrations, same Supabase project (or new one)
- **Design system:** Identical — copy tailwind.config.js

---

## File Locations (trava-2)

All source at: `/Users/hoeherp/development/playground/github/trava-2/Untitled/`

Critical files to study:
- `backend/app/logic/transformer.py` — the canvas generation engine
- `backend/app/logic/agent.py` — understand to avoid same mistakes
- `backend/app/core/prompts.py` — BOARD_JSON_SCHEMA contract
- `frontend/src/lib/hooks/useChat.ts` — SSE integration
- `frontend/src/components/canvas/BoardWrapper.tsx` — Excalidraw embed
- `frontend/src/lib/hooks/useExcalidrawHydration.ts` — image loading


Lessons from building trava-3 (useful for future skills and phases):

1. **Tools must return structured JSON, not formatted text.** When `booking_search` returned prose with URLs buried in it, the LLM consistently dropped URLs when restructuring into JSON for `board_add_items`. Switching to JSON output fixed this completely.

2. **Use `InjectedState` for IDs the LLM shouldn't control.** When `trip_id` was a normal tool parameter, the LLM hallucinated creative but fake IDs. `InjectedState("trip_id")` injects from agent state — invisible to the LLM.

3. **System prompt must be explicit about tool usage.** "Use tools when you can" is too weak. "NEVER make up hotel data, ALWAYS call booking_search" actually works.

4. **Sync HTTP calls inside async flows fail silently.** `search_tavily_image_sync()` (httpx sync client) called from within an async tool chain can block or timeout without clear errors.

5. **Excalidraw image hydration needs explicit re-triggering.** Images stored as URLs in `files[id].dataURL` require the hydration hook to fetch via proxy and convert to base64. This may not re-trigger on canvas reload events.

6. **Scraped Booking.com URLs contain session-bound params that break outside Playwright.** The `href` on property cards includes `aid`, `sid`, `label` params tied to the Playwright session. Fix: strip all query params with `urlparse`, then append only clean booking params (checkin/checkout/adults/rooms). Pattern from skills-try-out repo's `add_booking_params()`.

7. **Need standalone skill tests.** Testing skills through the full app (start backend → chat → wait for agent → check board) is too slow. A simple `python -m skills.booking.test "Lisbon" ...` that runs the skill directly is essential for iteration.

8. **`uvicorn --reload` doesn't watch `skills/` directory.** Skills live at the project root, outside `backend/`. Changes to skills require manual backend restart.

9. **Be careful with substring URL filters.** `"searchresults" in raw_url` was intended to catch closed-hotel redirect URLs (`/searchresults.html?closed_msg=...`) but matched ALL hotel URLs because Booking.com appends `&from=searchresults` to every href. Fix: check the URL **path** only (`"/searchresults" in urlparse(raw_url).path`). This was the root cause of the "only 1 hotel" bug.

10. **Always set `&lang=en-us` in Booking.com scraper URL.** Without it, Booking.com auto-detects locale from the server's IP/headers, returning Portuguese text ("Pontuado com 7,9" instead of "Scored 7.9"). Explicit locale ensures consistent English output.

11. **Extract pure functions for testability.** `search.py` had URL building, URL cleaning, and booking param logic all inline inside `search_booking()`. Extracting them into `build_search_url()`, `clean_hotel_url()`, and `append_booking_params()` made them independently testable — and the "only 1 hotel" bug (#9 above) now has a regression test. Pattern: if logic doesn't need I/O, pull it into a pure function.

12. **pytest.ini `pythonpath = .` is key for skill tests.** Skills live at the project root (`skills/`), not inside `backend/`. Setting `pythonpath = .` in pytest.ini lets `from skills.booking.search import ...` work from the project root without sys.path hacks.
