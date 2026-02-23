# Trava — The Travel Backend for AI Agents

## The idea

We're building a **platform that any AI agent can use to plan and book travel**. Our skills API provides hotel search, affiliate link generation, and hosted Excalidraw boards. Any agent — Claude, GPT, a custom LangGraph agent, whatever — calls our API, gets results with affiliate links baked in, and can push them onto a visual board.

**We make money every time someone books, regardless of which agent found the hotel.**

## What makes this special

The bet: AI agents will become the primary way people plan trips. When that happens, those agents need a travel backend — search, booking, visual planning. We are that backend.

- **Bring your own agent** — our skills are hosted APIs. Any agent can call them. We don't care what LLM powers it.
- **Affiliate links are built into the infrastructure** — every hotel result that flows through our API carries an affiliate link. The agent doesn't need to know or care about monetization.
- **Hosted Excalidraw boards** — agents can read/write visual trip boards via API. Cards with hotels, activities, itineraries — all with clickable affiliate links.
- **Agent-agnostic** — works with Claude, GPT, open-source models, custom agents. The skills API is the integration point.

## Phasing

**Phase 1 (now):** We provide both the agent AND the platform. Full web app — dashboard, chat panel, Excalidraw board. Our own LangGraph agent powered by Claude. This is the product while agent distribution isn't mainstream yet.

**Phase 2:** Open the skills as a public API. External agents can search hotels, generate affiliate links, and create/update boards. Our web app becomes one of many clients.

**Phase 3:** Marketplace of travel skills. Community or partners contribute new skills (flights, activities, car rentals). All monetized through affiliate infrastructure.

## How it works (end user)

1. Open dashboard, create a new board
2. Chat with the agent: "Find me a hotel in Lisbon for March 17-20"
3. Agent searches Booking.com, returns results with affiliate links
4. Agent places hotel cards on the Excalidraw canvas as a visual itinerary
5. User clicks a link to book — we earn commission

## How it works (external agent, future)

1. Agent calls `POST /api/skills/booking/search` with destination + dates
2. Gets back hotel results with affiliate links already embedded
3. Agent calls `POST /api/boards/{id}/elements` to place results on a hosted board
4. User opens the board URL, sees the visual itinerary, books via affiliate links

## Revenue

CJ Affiliate (Commission Junction) deep links for Booking.com. The affiliate link is injected at the API level — every hotel result that passes through our system is monetized, no matter which agent or client consumes it.

## Key files

- `architecture.md` — full technical architecture
- `plan.md` — migration steps and phases
