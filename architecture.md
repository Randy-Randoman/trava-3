# Architecture: Trava — Travel Planning with AI Agents + Excalidraw

## Context

We have a working app in **trava-2/Untitled** — Next.js + FastAPI + Excalidraw + Supabase, powered by a Gemini agent. It works end-to-end but has three core problems:

1. **Boards not reusable** — canvas is fully replaced every time, no iteration
2. **Agent blind to board** — can't read what's on canvas, can't reference or remove items
3. **Poor results/links** — generic Amadeus data, search-page URLs instead of real booking links

**trava-3** keeps the working frontend + infrastructure and replaces the agent layer. The big architectural shifts:
- **Incremental board updates** (append/remove, not full replace)
- **Agent board awareness** (can read + modify the board via tools)
- **Skills system** (modular, auto-discovered tool packages)
- **LangGraph agent** (LLM-agnostic, simple ReAct pattern)
- **Booking.com via Playwright** (real results with affiliate links)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 16 + React 19)                       │
│                                                         │
│  /dashboard          /board?trip=<id>                   │
│  ┌──────────┐       ┌────────────┬──────────────────┐   │
│  │ Board 1  │       │  Agent     │   Excalidraw     │   │
│  │ Board 2  │  ──►  │  Chat      │   Canvas         │   │
│  │ Board 3  │       │  (35%)     │   (65%)          │   │
│  │ + New    │       │            │                  │   │
│  └──────────┘       └────────────┴──────────────────┘   │
│         │                    │              │            │
│         │              SSE stream      auto-save/load   │
└─────────┼────────────────────┼──────────────┼───────────┘
          │                    │              │
┌─────────┼────────────────────┼──────────────┼───────────┐
│  BACKEND (FastAPI + LangGraph)                          │
│         │                    │              │            │
│    trips CRUD          LangGraph Agent   canvas CRUD    │
│                        ┌────────────┐                   │
│                        │  ReAct     │                   │
│                        │  Loop      │                   │
│                        ├────────────┤                   │
│                        │ Skills:    │                   │
│                        │ ┌─ booking (Playwright+CJ)     │
│                        │ ├─ board (add/remove/read)     │
│                        │ └─ web_search (Tavily)         │
│                        └─────┬──────┘                   │
│                              │                          │
│                   Board tools update canvas directly    │
│                   (no frontend transform step)          │
└──────────────────────────────┼──────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────┐
│  SUPABASE                    │                          │
│  - Auth (email/password)     │                          │
│  - profiles, trips (+ board_items JSONB), canvas_states │
│  - conversations, messages                              │
│  - RLS policies per user                                │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | Next.js 16, React 19, Tailwind CSS | Reuse trava-2 brutalist design system |
| **Canvas** | @excalidraw/excalidraw ^0.18 | Embedded React component, dynamic import |
| **Chat UI** | Custom SSE streaming | Reuse trava-2 ChatInterface + useChat hook |
| **Backend** | FastAPI + Python | API layer, same structure as trava-2 |
| **Agent** | LangGraph (Python) | Replaces trava-2's custom Gemini tool loop |
| **LLM** | Gemini via langchain-google-genai | Swappable — LangGraph supports any LLM |
| **Search** | Playwright (headless) | Browser-based Booking.com scraping |
| **Affiliate** | CJ deep links (existing deeplink.py) | Affiliate link wrapping |
| **DB** | Supabase (Postgres + Auth) | Reuse trava-2 schema + board_items |
| **Images** | Tavily image search | Reuse trava-2 approach |

---

## Board Management — The Core Change

### Problem (trava-2)

```
User: "Create the board"
→ Agent generates entire board JSON
→ Frontend calls POST /trips/transform
→ Transformer REPLACES all canvas elements
→ User's previous work is gone
→ Agent has no idea what's on the board
```

### Solution (trava-3)

The board is a **shared workspace** between user and agent. The agent interacts with it through tools, incrementally.

### board_items — Structured Board State

New JSONB column on the `trips` table tracks what the agent has placed:

```sql
ALTER TABLE trips ADD COLUMN board_items JSONB DEFAULT '[]'::jsonb;
```

Each item in the array:

```python
class BoardItem(BaseModel):
    id: str                    # Unique ID (short UUID, e.g. "a1b2c3d4")
    type: str                  # "stay", "activity", "flight"
    name: str                  # "Grand Hotel Lisbon"
    excalidraw_group_id: str   # Links to Excalidraw element group
    data: dict                 # Full payload (price, url, rating, imageUrl, bookingUrl, etc.)
    added_at: str              # ISO timestamp
```

- `id` — the agent references items by this ID ("remove item a1b2c3d4")
- `excalidraw_group_id` — maps to the groupIds on Excalidraw elements for this card
- `data` — full structured data so the agent can read back prices, ratings, URLs

### Board Tools

The agent uses these tools (defined in `skills/board/tools.py`):

| Tool | What it does |
|------|-------------|
| `board_read` | Returns structured summary of what's on the board |
| `board_add_items` | Appends new cards to the canvas below existing content |
| `board_remove_items` | Removes specific items by ID (filters elements by groupId) |
| `board_clear` | Removes all agent-placed items, preserves user-drawn content |

### Flow: Adding Items to Board

```
Agent calls board_add_items([{name: "Hotel A", price: "€150", ...}, ...])
  │
  ├─ 1. Read current canvas_state (elements + files) from DB
  ├─ 2. Read current board_items from trips table
  ├─ 3. For each new item:
  │     ├─ Generate Excalidraw card elements via transformer
  │     ├─ Position below existing content (max_y + gap)
  │     └─ Record BoardItem with excalidraw_group_id
  ├─ 4. APPEND new elements to existing canvas (not replace)
  ├─ 5. MERGE new files into existing files
  ├─ 6. Save canvas_state + board_items to DB
  └─ 7. Return "Added 3 items to the board"
       │
       └─ SSE sends canvas_updated event → frontend reloads canvas
```

### Flow: Reading the Board

```
Agent calls board_read()
  │
  ├─ Read board_items from trips table
  └─ Return formatted summary:
       "Board has 3 items:
        - [a1b2] STAY: Grand Hotel Lisbon (€150) Rating: 8.7
        - [c3d4] STAY: Lisbon Boutique (€95) Rating: 9.1
        - [e5f6] ACTIVITY: Fado Night Tour (€35)"
```

### Flow: Removing Items

```
Agent calls board_remove_items(["a1b2"])
  │
  ├─ Find excalidraw_group_id for item "a1b2"
  ├─ Filter out elements with that groupId from canvas
  ├─ Remove item from board_items
  ├─ Clean up orphaned files
  ├─ Save both
  └─ Return "Removed Grand Hotel Lisbon from board"
```

### Positioning Strategy

When adding new cards, the transformer:
1. Scans all existing elements to find the bounding box (max_y)
2. Starts placing new cards at `max_y + GAP`
3. Uses masonry layout (3-column grid) within that region

This preserves user-drawn content and previously placed cards. Users can drag cards to rearrange — the agent doesn't track positions.

### Edge Cases

| Case | Behavior |
|------|----------|
| User deletes a card on canvas | board_items still lists it. Agent may reference a "phantom" item. Acceptable for MVP. |
| User moves cards | No impact. Agent doesn't track x/y positions. |
| User draws freehand on canvas | Preserved. Agent only appends/removes its own element groups. |
| User edits text in a card | board_items keeps original data. Agent reads original, not edited text. |
| Agent adds in multiple rounds | Each round reads fresh canvas state, positions below existing content. |

---

## Skills System

### Design: Python-Native, No YAML

Each skill is a Python package in `skills/`. Convention over configuration:

```python
# skills/booking/__init__.py
from .tools import booking_search, deeplink_generate

TOOLS = [booking_search, deeplink_generate]
PROMPT = """You have access to Booking.com hotel search. Use booking_search to find
accommodations. Results include real prices, ratings, and affiliate booking links."""
```

The registry discovers skills automatically:

```python
# skills/__init__.py
import importlib, pkgutil

def load_all_skills():
    """Scan skills/ subpackages, collect TOOLS and PROMPT from each."""
    tools, prompts = [], []
    for importer, name, ispkg in pkgutil.iter_modules(__path__):
        if ispkg:
            mod = importlib.import_module(f".{name}", __package__)
            tools.extend(getattr(mod, "TOOLS", []))
            prompt = getattr(mod, "PROMPT", "")
            if prompt:
                prompts.append(prompt)
    return tools, "\n\n".join(prompts)
```

**Adding a new skill = adding a new folder.** No backend code changes.

### Skill Structure

```
skills/
├── __init__.py              # Registry: load_all_skills()
│
├── booking/                 # Hotel search + affiliate links
│   ├── __init__.py          # Exports TOOLS, PROMPT
│   ├── tools.py             # @tool booking_search, deeplink_generate
│   ├── search.py            # Playwright-based Booking.com scraping
│   ├── deeplink.py          # CJ affiliate link generation
│   └── models.py            # Hotel, SearchParams (Pydantic)
│
├── board/                   # Board management
│   ├── __init__.py          # Exports TOOLS, PROMPT
│   ├── tools.py             # @tool board_read, board_add_items, board_remove_items, board_clear
│   └── models.py            # BoardItem
│
└── web_search/              # General search + images
    ├── __init__.py          # Exports TOOLS, PROMPT
    └── tools.py             # @tool web_search, image_search (Tavily)
```

### Skill: booking

**tools.py** — thin wrappers around core logic:

```python
@tool
async def booking_search(
    destination: str,
    checkin: str,       # YYYY-MM-DD
    checkout: str,      # YYYY-MM-DD
    adults: int = 2,
    rooms: int = 1,
) -> str:
    """Search Booking.com for hotels. Returns results with prices, ratings, and affiliate booking links."""
    params = SearchParams(...)
    hotels = await search_booking(params, get_playwright_service())
    return format_results(hotels)  # Formatted text for the agent

@tool
def deeplink_generate(hotel_url: str, checkin: str, checkout: str, adults: int = 2, rooms: int = 1) -> str:
    """Generate an affiliate booking link for a specific hotel URL."""
    return build_affiliate_url(hotel_url, config, ...)
```

**search.py** — Playwright headless scraping of Booking.com. Extracts: name, price, rating, review_count, distance, URL. Returns structured Hotel objects.

**deeplink.py** — Wraps hotel URLs in CJ affiliate deep links:
```
https://www.anrdoezrs.net/click-{PID}-{AID}?url={encoded_booking_url}
```

### Skill: board

**tools.py** — board management tools that directly update canvas_state and board_items in the DB. See "Board Tools" section above for full details.

### Skill: web_search

**tools.py** — wraps Tavily API for general search and image search. Same as trava-2's tavily.py but as @tool functions.

---

## LangGraph Agent

### State

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Chat history
    trip_id: str                              # Current trip context
    user_id: str                              # Auth user
```

No board_data in state. Board tools handle canvas directly.

### Graph

Simple ReAct pattern:

```
START → agent_node → should_continue?
                        ├── tool calls → tool_node → agent_node (loop)
                        └── no tool calls → END
```

The agent decides when to call tools based on the conversation. No "create board" string matching — the agent naturally uses `booking_search` when asked to find hotels, and `board_add_items` when asked to put things on the board.

### Tool Loading

Tools are loaded from the skills registry at startup:

```python
from skills import load_all_skills

tools, skill_prompts = load_all_skills()
# tools = [booking_search, deeplink_generate, board_read, board_add_items, ...]
# skill_prompts = combined prompt fragments from all skills
```

The agent graph binds these tools. Adding a new skill automatically gives the agent new tools on next restart.

### System Prompt

Dynamic prompt that includes:
- Base personality and instructions
- Current date
- Skill prompts (auto-injected from all loaded skills)
- Board JSON schema reference (for structured output when placing items)

---

## SSE Streaming

### Event Format

```
event: status          → { content: "Searching hotels in Lisbon..." }
event: text            → { content: "I found 10 hotels..." }
event: canvas_updated  → { content: { trip_id: "..." } }
event: done            → {}
event: error           → { content: "Something went wrong" }
```

**Change from trava-2:** `board_data` event is replaced by `canvas_updated`. The frontend no longer calls `/trips/transform` — the board tools update the canvas server-side. Frontend just reloads when it gets `canvas_updated`.

### Frontend Handler (useChat.ts)

```typescript
// OLD (trava-2):
} else if (data.type === 'board_data') {
    await transformBoardData(tripId, data.content)  // Frontend transforms
    window.dispatchEvent(new CustomEvent('canvas-updated', ...))
}

// NEW (trava-3):
} else if (data.type === 'canvas_updated') {
    window.dispatchEvent(new CustomEvent('canvas-updated', { detail: { tripId } }))
    // Canvas already updated server-side. Just reload.
}
```

### How Board Tools Trigger canvas_updated

When a board tool (e.g. `board_add_items`) runs inside the LangGraph tool_node, it updates the DB. The chat.py streaming endpoint detects that a board tool was called and emits a `canvas_updated` SSE event after the tool completes.

---

## Database Schema

Reuse trava-2 schema + one addition:

```sql
-- Existing (from trava-2 migrations 001-004)
profiles(id UUID PK, username, avatar_url, created_at, updated_at)

trips(id UUID PK, user_id FK, title, status, destination,
      start_date, end_date, budget, currency, travelers, vibe,
      share_token, board_items JSONB DEFAULT '[]',  -- ★ NEW
      created_at, updated_at)

canvas_states(id UUID PK, trip_id FK UNIQUE,
              scene_elements JSONB, scene_files JSONB, scene_app_state JSONB,
              last_modified)

conversations(id UUID PK, trip_id FK UNIQUE, title, created_at, updated_at)

messages(id UUID PK, conversation_id FK, role TEXT, content TEXT, created_at)
```

RLS policies enforce per-user access. Cascade deletes on trip removal.

---

## Transformer Changes

The existing `transformer.py` from trava-2 is reusable. Key changes:

| Function | Status | Notes |
|----------|--------|-------|
| `create_card_group()` | **Keep as-is** | Core building block — generates one card's elements |
| `generate_excalidraw_scene()` | **Keep** | Used by `board_clear` + full regeneration |
| `generate_card_elements()` | **New** | Generates elements for N items, positioned below existing content |

### generate_card_elements() — New Entry Point

```python
def generate_card_elements(
    items: list[dict],
    existing_elements: list[dict],
    viewport_width: int = DEFAULT_VIEWPORT_WIDTH,
) -> tuple[list[dict], dict, list[str]]:
    """
    Generate Excalidraw elements for new items, positioned below existing content.

    Returns:
        new_elements: Elements to APPEND to canvas
        new_files: Files to MERGE into canvas
        group_ids: Group ID for each card (for board_items tracking)
    """
    # 1. Find max_y of existing elements
    # 2. Start masonry layout at max_y + GAP
    # 3. Call create_card_group() for each item
    # 4. Return new elements only (caller appends)
```

---

## Folder Structure

```
trava-3/
├── idea.md                          # Product vision
├── architecture.md                  # This file
├── plan.md                          # Implementation phases
├── learning.md                      # Learnings from trava-2
├── claude.md                        # Project conventions
│
├── frontend/                        # Next.js app (from trava-2)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # AuthProvider wrapper
│   │   │   ├── page.tsx             # 35% chat + 65% Excalidraw split
│   │   │   ├── dashboard/page.tsx   # Board list (grid of trip cards)
│   │   │   ├── login/page.tsx
│   │   │   └── api/image-proxy/route.ts
│   │   ├── components/
│   │   │   ├── canvas/BoardWrapper.tsx
│   │   │   ├── chat/ChatInterface.tsx, ChatBubble.tsx, InputArea.tsx
│   │   │   └── auth/ProtectedRoute.tsx
│   │   ├── lib/
│   │   │   ├── api.ts               # Backend fetch helpers
│   │   │   ├── supabase/client.ts
│   │   │   ├── auth/AuthContext.tsx
│   │   │   └── hooks/useChat.ts, useExcalidrawHydration.ts
│   │   └── types/
│   │       ├── message.ts
│   │       └── trip.ts
│   ├── tailwind.config.js           # Brutalist theme
│   └── package.json
│
├── backend/
│   ├── main.py                      # FastAPI app, CORS, route mounting
│   ├── requirements.txt
│   ├── migrations/
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_rls_policies.sql
│   │   ├── 003_chat_messages.sql
│   │   ├── 004_revise_chat_schema.sql
│   │   └── 005_board_items.sql      # ★ New: board_items on trips
│   └── app/
│       ├── api/
│       │   ├── chat.py              # ★ Rewrite: LangGraph SSE streaming
│       │   └── trips.py             # Copy from trava-2
│       ├── core/
│       │   ├── config.py            # Pydantic settings
│       │   ├── prompts.py           # ★ New system prompt for Claude
│       │   └── templates.py         # Welcome canvas template
│       ├── agent/
│       │   ├── graph.py             # ★ New: LangGraph StateGraph
│       │   └── state.py             # ★ New: AgentState TypedDict
│       ├── logic/
│       │   └── transformer.py       # ★ Adapt: add generate_card_elements()
│       └── services/
│           ├── database.py          # Copy + add board_items methods
│           └── playwright.py        # ★ New: headless browser manager
│
├── skills/                          # ★ New: skill modules
│   ├── __init__.py                  # Registry: load_all_skills()
│   ├── booking/
│   │   ├── __init__.py
│   │   ├── tools.py
│   │   ├── search.py
│   │   ├── deeplink.py
│   │   └── models.py
│   ├── board/
│   │   ├── __init__.py
│   │   ├── tools.py
│   │   └── models.py
│   └── web_search/
│       ├── __init__.py
│       └── tools.py
│
├── docker-compose.yml
└── .env
```

---

## Data Flow: User Searches for Hotels (new)

```
1. User types "Find me a hotel in Lisbon for March 17-20"
2. Frontend sends POST /chat/stream { message, trip_id }
3. Backend invokes LangGraph agent with message + history
4. Agent decides to call booking_search tool
5. booking_search → Playwright → Booking.com → structured Hotel results with affiliate links
6. Agent responds: "I found 10 hotels. Here are the top 5: ..."
7. Response streamed via SSE → chat panel updates
8. Backend sends board_ready SSE event → "Add to Board" button appears in chat panel
9. User clicks "Add to Board" button OR types "add those to the board"
10. Agent calls board_add_items with the hotel items
11. board_add_items → transformer generates cards → appends to canvas → saves to DB
12. SSE sends canvas_updated → frontend reloads canvas
13. User sees hotel cards on Excalidraw with clickable affiliate links
14. User: "Remove the second one, it's too expensive"
15. Agent calls board_read (knows what's on board), then board_remove_items
16. Card removed from canvas, board_items updated
```

### "Add to Board" Button

Reused from trava-2. A teal button that appears in the chat panel when the backend signals `board_ready` (after search results are returned). When clicked, it sends a message to the agent triggering `board_add_items`. Users can also trigger this via chat ("add those to the board").

---

## API Endpoints

### Frontend (Next.js)
| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/image-proxy?url=<url>` | CORS proxy for external images |

### Backend (FastAPI)
| Method | Route | Purpose | Status |
|--------|-------|---------|--------|
| POST | `/chat/stream` | SSE streaming chat | ★ Rewrite for LangGraph |
| GET | `/chat/messages/{trip_id}` | Load message history | Copy |
| POST | `/trips` | Create trip + welcome canvas | Copy |
| GET | `/trips` | List all user trips | Copy |
| GET | `/trips/{trip_id}` | Get trip metadata | Copy |
| PATCH | `/trips/{trip_id}` | Update trip | Copy |
| DELETE | `/trips/{trip_id}` | Delete trip (cascades) | Copy |
| GET | `/trips/{trip_id}/canvas` | Load Excalidraw scene | Copy |
| PUT | `/trips/{trip_id}/canvas` | Save Excalidraw scene | Copy |

**Removed:** `POST /trips/transform` — no longer needed. Board tools handle transformation server-side.

---

## Reuse from trava-2

| Component | Action | Changes |
|-----------|--------|---------|
| All frontend components | Copy | None (except useChat.ts) |
| `useChat.ts` | Copy + adapt | Replace board_data handler with canvas_updated |
| `tailwind.config.js` | Copy | None |
| `database.py` | Copy + extend | Add board_items read/write methods |
| `transformer.py` | Copy + extend | Add generate_card_elements() |
| `trips.py` (API) | Copy | Remove /trips/transform endpoint |
| `config.py` | Copy + adapt | New env vars (ANTHROPIC_API_KEY, CJ creds) |
| `templates.py` | Copy | None |
| `migrations 001-004` | Copy | None |
| All TypeScript types | Copy | None |

---

## Environment Variables

```env
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# LLM
GEMINI_API_KEY=

# Affiliate
CJ_PID=
CJ_AID=

# Search
TAVILY_API_KEY=

# Frontend
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## Not Covered (Future)

- Flight search skill
- GetYourGuide / activities skill
- Board reconciliation (sync board_items when user deletes cards on canvas)
- Multi-user collaboration
- Production deployment (Railway/Vercel)
- Proper JWT auth (currently X-User-ID header)
- Skill marketplace / external agent API (Phase 2-3 of the big vision)
