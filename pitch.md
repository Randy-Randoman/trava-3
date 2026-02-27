# Pitch Development

Working document for developing the TRAVA pitch deck.

## Core Positioning

**Travel planning is broken — especially for groups.**

TRAVA is the **visual planning canvas for travel** — powered by AI, built for collaboration.

- Beachhead: Group travel planning (2-6 people need visual coordination most)
- Phase 1: Full product (our agent + visual canvas) → get traction
- Phase 2: "Bring your own agent" → we become the visual layer, not another chatbot
- This shifts us from "AI travel agent #47" to "the place where travel plans come to life"

## What's OUT (vs old deck)

- "Share & Earn" loop — not part of the new idea
- Tipping culture revenue stream
- Positioning as a social/sharing platform

## What's IN

- Visual canvas as the core differentiator (Excalidraw-based)
- Group collaboration on the canvas
- Agent-agnostic platform (Phase 2)
- Affiliate revenue at the infrastructure level
- Distribution via agent ecosystems (MCP servers, public API, etc.)

## Core Belief

**Planning should be fun.** It creates the anticipation for the trip. The visual canvas isn't just more functional — it turns planning from a chore into part of the experience. You're building a moodboard of your future trip together. That's exciting.

## Risk / Answer Framework

| Risk | Accelerator will ask... | Our answer |
|------|------------------------|------------|
| Low frequency | "People plan 1-3 trips/year. How do you retain?" | High value per trip (€40-240 rev). City activities/outings as expansion. Travel is low-frequency but high-value. |
| Group adoption friction | "How do you get 5 friends on a new platform?" | Shareable link, no sign-up. Only the organizer needs an account. Everyone else gets view access via link. (Figma model.) |
| Is visual planning real? | "Do people actually want a canvas for this?" | Planning should be fun — it creates anticipation. People love travel vlogs, holiday pics, mood boards. A visual canvas makes planning part of the excitement, not a chore. |
| Google competition | "Google has AI Mode Canvas for travel." | We checked — it's a list + map, not editable, no collaboration. We're differentiated. |
| Affiliate fragility | "What if Booking.com changes terms?" | Multi-provider strategy (Booking, Expedia, GetYourGuide, Viator). Phase 2 aligns OTA incentives — we drive bookings to them via agents. |
| "Just another AI travel app" | "How are you different from Mindtrip, Layla?" | Phase 1 yes, but Phase 2 shifts us to BYOA. We become the visual layer, not another chatbot. No competitor offers this. |

## Open Questions

- [x] Competitive landscape — researched (see below)
- [x] Risk framework — documented above
- [ ] Revenue model for Phase 2 — pure affiliate confirmed, but worth exploring API fees later?
- [ ] What demo assets do we have for the deck?

---

## Competitor Research (Feb 2026)

### The Big Insight

TRAVA sits at an intersection **nobody occupies**:

```
                    Visual/Canvas Planning
                           ▲
                           │
                    Miro ● │           ● TRAVA
               Pinterest ● │
                           │
  No AI ◄──────────────────┼──────────────────► AI-Powered
                           │
            Wanderlog ●    │    ● Mindtrip
              Troupe ●     │    ● Layla AI
             TripIt ●      │    ● GuideGeek
                           │
                           ▼
                    List/Chat Planning
```

- **AI travel tools** → all output lists or chat. No visual canvas.
- **Visual tools** (Miro, Pinterest) → no travel features, no booking, no AI.
- **Collaborative trip planners** (Wanderlog, Troupe) → lists + maps, no freeform canvas.
- **"Figma for trip planning" does not exist yet.** TRAVA is it.

---

### Category 1: AI Travel Agents

These solve the same user problem but with text/lists.

| Tool | Planning UX | Group Collab | Visual Canvas | Booking | Revenue | BYOA/API |
|------|------------|-------------|--------------|---------|---------|----------|
| **Mindtrip** | Chat + structured itinerary + map. Polished. Can import from TikTok/IG. | Yes — real-time editing, comments, expense split | No. Pretty cards but no freeform canvas. | Affiliate (Priceline, Viator) | Free + B2B white-label. $3.6M rev. $19M raised (Amex, Capital One, United Airlines Ventures) | No API. No BYOA. |
| **Layla AI** (acquired Roam Around) | Chat + day-by-day itinerary + map. Reels-style video previews. PriceLock price tracking. | Limited — share/export only | No | Affiliate (Booking, Skyscanner, Viator, Kayak) | Freemium $49/yr | No API. No BYOA. |
| **Wanderlog** | List + map. Google Docs-style editing. Route optimization. | **Best-in-class** — real-time editing, voting, chat, expense split | No. Map sidebar, but list-first. | Affiliate (Booking, Expedia, Airbnb) | Freemium $80/yr. ~$1M rev. Bootstrapped. | No API. No BYOA. |
| **Wonderplan** | Dashboard + map. Drag-and-drop. AI recalculates logistics. | Yes — multi-user editing | No freeform canvas. Structured dashboard. | None | Free (pre-monetization?) | No API. Possible future. |
| **GuideGeek** (Matador Network) | Chat only (WhatsApp/IG/Messenger). No structured UI. | No | No | None | B2B white-label for DMOs | White-label. No dev API. |
| **Vacay Chatbot** | Chat with themed advisors | Limited | No | None | Freemium $10/mo. B2B white-label. | White-label. No dev API. |
| **Airial** (2025, ex-Meta) | Chat + map. Logistics-focused (transfer times, wait times). TikTok import. | Yes | No | Pre-revenue | $3M seed | No API. Early stage. |
| **Google AI Mode + Canvas** | Search-integrated. New Canvas tool for visual trip org. Agentic restaurant booking. | No trip collab | New "Canvas" tool — early, integrated into Search, not standalone | Deep (Flights, Hotels, OpenTable, Resy) | Ad-supported | Gemini API available |
| **Kayak AI Mode** | Chat overlay on Kayak search | No | No | Kayak meta-search | Existing affiliate model | Existing affiliate APIs |
| **TripAdvisor AI Planner** | Chat + structured itinerary (OpenAI-powered). 1B+ reviews. | Share & edit | No | Viator, TheFork. $840M Viator revenue (2024). | Ad/affiliate. $1.84B total rev. | B2B white-label. No dev API. |

**Key takeaway:** Everyone builds a better chatbot. Nobody builds a visual canvas. Wanderlog has best group features but is list-first. Mindtrip is most polished but no creative control.

---

### Category 2: Collaborative & Visual Planning Tools

These have the group/visual angle but miss AI and travel-specific features.

| Tool | Visual/Canvas | Group Collab | AI | Booking | Notes |
|------|--------------|-------------|-----|---------|-------|
| **Miro** | **Best freeform canvas.** Infinite whiteboard, stickies, images. | Excellent real-time collab | Generic AI, not travel | None | Not a travel product. $20/mo. |
| **Pinterest boards** | Visual grid of pins. Place Pins add map. | Group boards (add-only) | Recommendations only | No | Inspiration tool, not planning tool. |
| **Polarsteps** | Beautiful map visualization + photos | **No collaboration** (most-requested feature) | New AI itinerary builder (2025, uses Claude) | Affiliate | 18M users. Primarily post-trip tracking. |
| **TripIt** | List/timeline only | Limited sharing | Minimal | No booking, aggregates confirmations | Owned by SAP Concur. $49/yr. |
| **Notion for travel** | Flexible but DIY. No map, no travel features. | Strong real-time collab | Generic AI | None | General-purpose tool. |
| **Troupe** (JetBlue) | No canvas. Polls/voting interface. | Core feature — polling, voting, RSVPs | AI accommodation search | Vrbo partnership | Free (JetBlue-backed). Group decision tool. |
| **Pilot** | Map-based itinerary | Shared trips, real-time | AI quickstart | Group hotel booking + affiliate | Free. "Pay what you want." |
| **Sygic/Tripomatic** | Map-based planning with POIs | Basic invite-friends | AI itinerary generator | Tour/activity links | Freemium $19. B2B data licensing. |

**Key takeaway:** Miro has the canvas but isn't a travel product. Polarsteps has 18M users with beautiful visuals but zero collaboration. Nobody combines canvas + collab + travel + booking.

---

### Category 3: Agent Tool Platforms (Phase 2 landscape)

This is where TRAVA competes when we open up the BYOA/API.

**MCP is THE standard.** Anthropic created it, then donated it to the Linux Foundation (Dec 2025). Co-founded with OpenAI, Google, Microsoft, AWS, Bloomberg, Cloudflare. Both Claude and ChatGPT support MCP.

**Travel MCP servers that already exist:**

| Provider | What | Type |
|----------|------|------|
| Booking.com | Hotels, multi-domain | Official, ChatGPT launch partner |
| Expedia | Hotels, flights, activities, cars | Official |
| Kiwi.com | Flight search + booking links | Official |
| Sabre | Flights, hotels, cars (50PB data) | Official |
| Agoda | Hotels (open-source MCP server) | Official |
| TourRadar | 50K+ multi-day tours | Official |
| Peek | Real-time activities/tours | Official |
| Turkish Airlines | Flights + loyalty | Official |
| lastminute.com | Flights (hotels planned) | Official |
| Airbnb | Listing search | Unofficial/community |

**Generic agent platforms:**

| Platform | Travel tools? | Model |
|----------|--------------|-------|
| Composio | Minimal (Bookingmood, Planyo) | SaaS $29+/mo. Managed, not a marketplace. |
| Toolhouse | None | SaaS $10/mo |
| LangChain | Amadeus integration only | Open source. No revenue share. |
| CrewAI | None. Travel is a "use case." | Open source + enterprise SaaS. |
| OpenAI GPT Store | Booking.com, Expedia as launch partners | Opaque revenue share ($500-$15K/mo for top GPTs) |

**Emerging: WebMCP** — Google/Microsoft proposal (Chrome 145+, Feb 2026) for websites to expose structured tools to in-browser AI agents. Travel is a primary use case. 12-18 months from broad adoption.

**Key takeaway:** Big OTAs are building their own MCP servers, but they're siloed (Booking.com only shows Booking.com). **Nobody is building the visual layer.** Agents can search hotels via MCP, but they have nowhere to PUT the results visually. TRAVA's visual boards could be the missing piece in the MCP ecosystem.

---

## Differentiation Matrix

What makes TRAVA unique across ALL categories:

| Capability | AI Agents (Mindtrip, Layla...) | Collab Tools (Wanderlog, Troupe...) | Canvas Tools (Miro, Pinterest...) | MCP/OTA APIs | **TRAVA** |
|------------|-------------------------------|-------------------------------------|----------------------------------|-------------|-----------|
| AI-powered planning | Yes | Some | No | Search only | **Yes** |
| Visual freeform canvas | No | No | Yes (but no travel) | No | **Yes** |
| Group collaboration | Some | Yes | Yes | No | **Yes** |
| Real hotel data + booking | Affiliate links | Limited | No | Yes (siloed) | **Yes** |
| Bring your own agent | No | No | No | N/A (they ARE the API) | **Yes (Phase 2)** |
| Agent-agnostic platform | No | No | No | Each is one provider | **Yes (Phase 2)** |

**TRAVA is the only product that combines: visual canvas + AI + group collab + real booking + agent-agnostic platform.**

---

## Strategic Insights for the Pitch

### 1. The canvas IS the moat
Everyone can build another chatbot. The visual planning surface — collaborative, real-time, with booking links on the cards — is what no one else has. This is what we should lead with.

### 2. "BYOA" is a blue ocean
Zero competitors offer bring-your-own-agent. Every AI travel tool is locked to its own LLM. Phase 2 positions us as infrastructure, not another consumer app fighting Mindtrip for users.

### 3. MCP is the distribution channel for Phase 2
Build TRAVA's visual boards as an MCP server. Any agent (Claude, ChatGPT, custom) can push travel results onto a TRAVA board. We become the "display layer" for AI travel — like how a monitor doesn't care which computer is plugged in.

### 4. The OTA MCP gap
Booking.com has an MCP server for search. Expedia has one. But they're siloed and output raw data. Nobody aggregates across sources, and nobody provides a visual destination for the results. TRAVA could be the visual aggregation layer.

### 5. Polarsteps is a comp, not a competitor
18M users, beautiful visual maps, travel-specific. But no collaboration and no AI planning. They prove the demand for visual travel experiences. We serve a different use case (planning vs. tracking) but validate the market.

### 6. Wanderlog is the closest competitor
Best group features, map-based, has AI. But fundamentally list-first. No canvas. $1M revenue, bootstrapped, 5-person team. This is the benchmark to beat on collaboration — and differentiate on the visual experience.

---

## Pitch Deck Structure (Draft)

### Slide 1: Title
**TRAVA** — Make Trip Planning Fun Again.
(Alternative: "Plan Trips You Can't Wait To Take" / "Where Trips Come To Life")

### Slide 2: Problem — Travel planning is broken
Same energy as old deck — relatable, emotional. The 4 boxes: Disconnected, Time Sink, Decision Paralysis, Group Chaos. Keep the memes. Keep "73% of leisure travel is group travel."
Add: "62% of Gen-Z/Millennials already use AI to plan — but still end up with lists and 15 open tabs."

### Slide 3: Solution — TRAVA
What if planning was the fun part?
- Tell the AI what you want → it builds a visual board: flights, hotels, activities, transport, local spots, tips — your whole trip
- Share a link with your group — no sign-up needed. Everyone sees the same board.
- Discuss, rearrange, decide together. Click to book.
- Planning creates anticipation. TRAVA makes it visual, collaborative, exciting.

### Slide 4: Why visual?
Side-by-side comparison: left = what AI travel tools give you today (a text list). Right = what TRAVA gives you (the visual board).

Key points (pick 2-3, don't overload):
- A list says "Hotel A, €120." A card with a rooftop pool photo makes you *feel* the trip.
- Groups can't align on text — "which one was the second hotel?" On a board, you point at the same thing.
- Organize spatially: by day, by neighborhood, by vibe. A trip isn't linear. A list is. Everyone plans differently.
- It's the difference between a spreadsheet and a mood board. Same info — one creates excitement.
- **Planning should feel like the start of the adventure, not homework.**

(This slide should be very visual itself — show, don't tell. Maybe a screenshot of a boring ChatGPT list on the left vs. a TRAVA board on the right.)

### Slide 5: Product demo
Screenshot/GIF of the working prototype. Split-screen: chat + Excalidraw board with trip cards.

### Slide 5: The bigger vision (Phase 1 → Phase 2)
- Phase 1 (now): Our agent + our canvas. Full product. Get traction, validate.
- Phase 2: Bring your own agent. Any AI agent can push results to TRAVA boards via API/MCP.
- We shift from "AI travel app" to "the visual layer for travel planning with AI agents."
- Cuts our token costs, opens distribution to every agent in the ecosystem.

### Slide 7: Competitive landscape
The 2x2 chart (Visual ↔ List, AI ↔ No AI). TRAVA in the empty quadrant.
Brief comparison: Mindtrip (polished but no canvas), Wanderlog (great collab but list-first), Miro (canvas but not travel).
"Nobody combines: visual canvas + AI + group collab + real booking."

### Slide 8: Market opportunity

**TAM: $2.6B** — Group travel planning apps market (WiseGuy Reports, 2025). Growing to $6.5B by 2035 (9.6% CAGR).
Context: within a $391B global group travel market (MRFR, 2025).

**SAM: ~$500-750M** — Affiliate commission pool from European Gen-Z/Millennial group travel.
(€104B European online travel × 25% group × 50% Gen-Z/Millennial × 4-5% affiliate rate)

**SOM: €1-4M ARR** — Year 3 target. Benchmarked against:
- Wanderlog: $1M ARR with 5 people, only $1.65M raised
- Layla AI: $2.8M revenue with 25 people, $3.36M raised

**Why now:**
- 62% of Gen-Z/Millennials already use AI for travel planning (Phocuswright/Accenture, 2024)
- 48% of European travelers have used AI tools for travel, +7pp YoY (MMGY, 2025)
- MCP standard adopted by Anthropic, OpenAI, Google, Microsoft — agents need visual tools
- The visual layer for AI travel doesn't exist yet

### Slide 9: Business model

Affiliate commissions baked into every result — flights, hotels, activities, transport, experiences.

| | Rate | Source |
|-|------|--------|
| Hotels (Booking.com) | 4-6% of booking | Booking.com affiliate program |
| Activities (GetYourGuide/Viator) | 7-8% of booking | GYG/Viator affiliate programs |
| Flights (Kiwi.com) | ~3% of ticket | Kiwi affiliate program |

**Unit economics (per trip):**

Cost side:
- LLM API cost per board: **~€0.17** (measured: €0.85 for 5 boards)
- Assume 1-2 sessions per trip, ~15-25 messages total
- Hosting/scraping: negligible at early scale
- **Total cost per trip: ~€0.20-0.50**

Revenue side (avg European group trip, 4 people × €1,500 pp = €6,000 total):

| Scenario | % booked through us | Revenue @ 5% avg commission | Margin |
|----------|--------------------|-----------------------------|--------|
| Pessimistic (5%) | €300 | **€15** | €14.50+ |
| Moderate (15%) | €900 | **€45** | €44.50+ |
| Optimistic (30%) | €1,800 | **€90** | €89.50+ |

Even the pessimistic case is 30x+ margin on cost.

Key insight: **In Phase 2 (BYOA), our cost drops to near zero** — external agents pay their own LLM costs. We only host the board and serve affiliate links.

Note: The % booked through us is the key metric to validate early.

**Future upside: agentic booking.**
Today users click a link and book manually — drop-off at every step. Tomorrow, agents execute bookings directly (Google is already building this for restaurants, Booking.com and Expedia are MCP partners). When that happens: user clicks "Book" on the board → agent handles everything → conversion jumps dramatically. The visual board becomes the checkout interface, not just the planning tool.

Caveat: Affiliate revenue arrives 1-6 months post-travel. Cash flow is delayed but margins are high.

**Benchmarks:**
- Wanderlog: $1M ARR, 5 people, $1.65M raised
- Layla AI: $2.8M revenue, 25 people, $3.36M raised
- Both validate affiliate-only revenue works at startup scale

### Slide 10: Team
Josh + Pitt. Same as old deck. "Built by Explorers — We ARE Our Users."

### Slide 11: The Ask
- Affiliate partnerships (Booking.com, Expedia, GetYourGuide, Viator, etc.)
- Distribution partners (agent platforms, MCP ecosystem, travel communities)
- Mentoring on go-to-market and travel industry

### Slide 12: Contact
Emails, QR codes.
