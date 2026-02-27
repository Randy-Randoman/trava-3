# Trava — The Visual Layer for Trip Planning

## Why

Trip planning is broken — especially for groups. It's scattered across tabs, apps, and group chats. AI is making it faster but not better: every AI travel tool outputs a text list. Nobody builds the visual, collaborative surface where trips actually come to life.

Planning should feel like the start of the adventure, not homework. A visual moodboard of your upcoming trip creates anticipation — that's what people love about travel content. We bring that to planning.

## Beachhead: Group travel

73% of leisure travel is group travel. Groups need the visual canvas most — you can't coordinate 4-6 people over text lists in WhatsApp. One person creates the board, shares a link, everyone sees the plan. No sign-up needed. (Figma model.)

## The platform vision

Phase 1 we provide our own agent + the canvas. Full product to get traction. But as soon as possible we shift to **Bring Your Own Agent** — any AI agent can push travel results onto a TRAVA board via API/MCP. This moves us from "another AI travel agent" to "the visual layer for AI travel." Our token costs drop to near zero, distribution opens to the entire agent ecosystem. MCP servers for Booking.com, Expedia, Kiwi already exist — but agents have nowhere to PUT the results visually. We are that layer.

---

## The idea (technical)

We're building a **platform that any AI agent can use to plan and book travel**. Our skills API provides hotel search, affiliate link generation, and hosted Excalidraw boards. Any agent — Claude, GPT, a custom LangGraph agent, whatever — calls our API, gets results with affiliate links baked in, and can push them onto a visual board.

**We make money every time someone books, regardless of which agent found the hotel.**

## What makes this special

The bet: AI agents will become the primary way people plan trips. When that happens, those agents need a travel backend — search, booking, visual planning. We are that backend.

- **Bring your own agent** — our skills are hosted APIs. Any agent can call them. We don't care what LLM powers it.
- **Affiliate links are built into the infrastructure** — every result (flights, hotels, activities, transport) that flows through our API carries an affiliate link. The agent doesn't need to know or care about monetization.
- **Hosted Excalidraw boards** — agents can read/write visual trip boards via API. Cards with flights, hotels, activities, local spots, tips — all with clickable affiliate links.
- **Agent-agnostic** — works with Claude, GPT, open-source models, custom agents. The skills API is the integration point.

## Phasing

**Phase 1 (now):** We provide both the agent AND the platform. Full web app — dashboard, chat panel, Excalidraw board. Our own LangGraph agent powered by Claude. This is the product while agent distribution isn't mainstream yet.

**Phase 2 (BYOA):** Bring your own agent. Open the skills + visual boards as a public API / MCP server. External agents can search, generate affiliate links, and push results onto hosted boards. Our token costs drop to near zero.

**Phase 3:** Agentic booking. Users click "Book" on the board, the agent handles the full booking flow. Conversion jumps because booking through us becomes the easiest path.

## How it works (end user)

1. Open dashboard, create a new board
2. Chat with the agent: "Plan a 5-day trip to Lisbon for 4 friends, mid-range budget"
3. Agent searches flights, hotels, activities — returns results with affiliate links
4. Agent places cards on the Excalidraw canvas — images, prices, ratings, booking links
5. Share the board link with your group — no sign-up needed
6. Discuss, rearrange, decide. Click to book — we earn commission

## How it works (external agent, future)

1. Agent calls `POST /api/skills/booking/search` with destination + dates
2. Gets back hotel results with affiliate links already embedded
3. Agent calls `POST /api/boards/{id}/elements` to place results on a hosted board
4. User opens the board URL, sees the visual itinerary, books via affiliate links

## Revenue

Affiliate commissions across multiple providers:
- Hotels: Booking.com, Expedia (4-6%)
- Activities: GetYourGuide, Viator (7-8%)
- Flights: Kiwi.com (3%)

The affiliate link is injected at the API level — every result that passes through our system is monetized, no matter which agent or client consumes it.

## Unit economics

- Cost per board (LLM): ~€0.17 | Phase 2 (BYOA): near zero
- Avg group trip value: €6,000 (4 people × €1,500 pp)
- Revenue per trip: €15-90 depending on booking conversion
- Future upside: agentic booking removes friction, conversion increases

## Key files

- `pitch.md` — pitch deck development, competitor research, market data
- `architecture.md` — full technical architecture
- `plan.md` — migration steps and phases
- `learning.md` — learnings from trava-2
