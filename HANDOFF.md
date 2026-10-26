# Handoff: Phase 10 (publish-ready cleanup) + Phase 11 (MCP server)

All 17 issues (#42–#58) are implemented on `dev`, which is 29 commits ahead of `main`. Nothing is pushed yet.

**Test state at the end of the run**

| Suite | Result |
|---|---|
| Backend unit (`cd backend && python -m pytest tests/unit`) | 153 passed |
| Backend integration (`… tests/integration`) | 29 passed against local Supabase (2026-10-26) |
| Frontend (`npm test`) | 42 passed |
| `npm run lint` | 0 errors, 37 warnings (`any` + React 19 effect rule, downgraded on purpose) |
| `npx tsc --noEmit` | clean |
| `npm run build` | OK |

**Update 2026-10-26:** after a Docker restart, all migrations (001–011) applied cleanly on a local stack and all 29 integration tests pass. The first live run found a real bug: sign-up failed on every fresh install (`handle_new_user` used an unqualified `profiles`), fixed in migration 011. Also verified on 2026-10-26:
- **Docker:** both images build. The backend runs as `trava` and launches Chromium; `/health` is ok and `/mcp` answers 401. The frontend serves pages with the anti-framing headers.
- **OAuth + MCP end to end:** against the local Supabase OAuth server (enabled in `supabase/config.toml`), 19/19 checks pass. The checks cover discovery, dynamic client registration, PKCE with `resource`, consent, token exchange, the MCP tools, token separation, and revocation taking effect at once. supabase/auth#2820 did not reproduce locally.
- **Still untested:** a real client (Claude Code, claude.ai, ChatGPT) against a hosted deploy.

---

## 0. Do these first

1. **Add `SUPABASE_URL` to your root `.env`** (same value as `NEXT_PUBLIC_SUPABASE_URL`). The backend no longer reads `NEXT_PUBLIC_SUPABASE_URL` and won't start without it. `AUTH_ENABLED` and `AMADEUS_*` in your `.env` are unused and can go.
2. **Restart Docker Desktop**, then:
   ```bash
   supabase start                      # local stack on ports 553xx
   supabase db reset                   # applies migrations 001–010
   cd backend && python -m pytest tests/integration -v
   ```
   Expect a few first-run fixes. One known risk: the local stack may sign JWTs with HS256 only. If `test_api_flow` returns 401, either override `require_auth` in that test or run `supabase gen signing-key` and set `[auth] signing_keys_path` in `supabase/config.toml`.
3. **Live Supabase:** apply migrations **008, 009, 010 and 011** (`supabase link` + `supabase db push --dry-run`, then without `--dry-run`). If an old `user_feedback` table exists, drop it by hand.

## 1. Per-issue checks (open X, do Y, expect Z)

### Phase 10: cleanup
- **#42 restructure:** `cd backend && uvicorn main:app --reload` starts, and the agent loads the board, booking and web_search skills.
- **#43 approval removed:** sign up as a new user, expect to land on the dashboard with no "pending approval" step. In the Supabase SQL editor, as user B, try to read user A's trip: expect 0 rows.
- **#44 image proxy:** dashboard thumbnails and board card images load. `curl "localhost:3000/api/image-proxy?url=http://169.254.169.254/"` returns 403.
- **#45 feedback and callback removed:** sign up, log in and log out all work, and the feedback button is gone.
- **#46 dependencies:** `cd frontend && npm ci` works without `--legacy-peer-deps`.
- **#47 backend hardening:** chat works with `LLM_PROVIDER=google` and with `LLM_PROVIDER=anthropic` (`claude-sonnet-5-5`). The budget panel shows `1.234,50 €` as 1234.50.
- **#49 frontend fixes:** chat streams, the board updates after the agent adds cards, and the Excalidraw styling looks unchanged (its CSS now comes from the package).
- **#51 Docker and Railway:**
  - `docker compose build` runs without legacy-peer warnings.
  - `docker compose up`, then `curl localhost:8000/health` returns ok.
  - `docker compose exec backend whoami` prints `trava`.
  - Chromium launches inside the container, and a Booking search works there.
- **#52 docs:** follow the README on a fresh clone; every command works.

### Phase 11: MCP
- **Setup (manual):**
  - In Supabase → Authentication → OAuth Server: turn it on, set the authorization path to `/oauth/consent`, and allow dynamic client registration.
  - Make sure the JWT signing key is asymmetric (ES256/RS256).
  - Set `PUBLIC_BASE_URL` to the backend's exact public URL. Other Host headers get a 421.
- **#53 stable IDs:** ask the agent to search hotels, add them, add more, then remove one of the first ones by the ID `board_read` showed. Expect it to be removed.
- **#54 OAuth:**
  - Run `claude mcp add --transport http trava <PUBLIC_BASE_URL>/mcp`. The browser opens, you log in and see the consent page with Allow/Deny. Click Allow, and the server is connected.
  - Open `/settings/connections`, where the client is listed. Click Disconnect: the next tool call fails.
- **#55 MCP server:** in Claude Code, ask it to "list my trips", then "create trip Lisbon and add 3 hotels under €150 for 12–15 May". Open the trip in the app and the cards are there.
- **#56 save conflicts:** open the same trip in two tabs and change the board in tab A (or via MCP). Tab B shows a notice and reloads, and no cards are deleted.
- **#57 live updates:** with the board open, add items via MCP. The cards appear within a few seconds without a page reload.
- **claude.ai / Cowork / ChatGPT:** these need a public HTTPS backend (for example Railway). Add `<PUBLIC_BASE_URL>/mcp` as a custom connector and run the same flow.

## 2. needs-human

None of the issues were blocked, but these were **never run** because of Docker:
- the integration tests (#50, #54, #55, #56);
- migrations 008, 009 and 010;
- the container builds (#51).

On top of that, the real OAuth flow, Realtime delivery under owner-only RLS, and ChatGPT connector compatibility are untested.

## 3. Review findings not fixed (judgement calls, all low)

- **Image proxy:**
  - There's a DNS-rebinding gap between the address check and the fetch; closing it needs a pinned-IP dispatcher.
  - A 3xx response without `Location` returns the 3xx as JSON.
  - A DNS failure returns 500.
- **Backend style:**
  - `trips.py` repeats the same try/except about 10 times (one exception handler would do).
  - Loggers use f-strings.
- **Tests:**
  - The `test_budget.py` fixture duplicates `test_share.py`'s.
  - The board tests run twice: once against each tool and once against its plain function.
- **SSE parsing:** a malformed `data:` line now throws (intended), and there's no final flush (the backend always ends events with `\n\n`).
- **Canvas saves:**
  - A spurious "last edit wasn't saved" notice is possible when saves race (no data loss).
  - The 409 body carries the canvas, but the frontend re-fetches it anyway.
  - The notice's timer isn't cleared.
- **Board items:** `excalidraw_group_id` and `added_at` are still reset on every add.
- **OAuth:**
  - Someone who signs up mid-connect lands on the dashboard and has to reconnect from the client.
  - The root RFC 9728 URL advertises `…/mcp`.
  - There's no warning when `PUBLIC_BASE_URL` falls back to localhost.
  - PostgREST still accepts agent tokens directly (inherent to Supabase).
- **MCP:** agent tool calls have no rate limiting, so Booking scraping and Tavily costs are on you.
- **Upstream:** supabase/auth#2820 may break the consent step for some public MCP clients.
- **Dependencies:** 11 non-critical npm advisories come in through Excalidraw (accepted). Transitive Python dependencies aren't fully pinned.

## 4. Fixes made during merge and review (beyond the issues)

- Local Supabase ports moved to 553xx so the stack doesn't clash with another project's.
- Image proxy: also blocks CGNAT, reserved, multicast, NAT64 and 6to4 ranges.
- The budget parser reads `1.500 €` as 1500.
- Integration tests skip instead of hanging when Docker is unresponsive.
- Canvas saves: the version check and the write are now one atomic update, and a reload cancels any pending autosave.
- Auth:
  - `safeNextPath` blocks open redirects that use tabs or newlines;
  - JWKS is refetched only for an unknown `kid`, with a 60 s cooldown;
  - the app API rejects agent tokens;
  - the grant check runs off the event loop;
  - every page sends frame-blocking headers.
- MCP:
  - only `/mcp` is routed to the MCP app (not everything under `/`);
  - search errors are generic, with details only in the server log;
  - booking dates and guest counts are validated;
  - item IDs must be at least 4 characters.

## 5. Next

- Push `dev` and open one PR from `dev` to `main`.
- Possible follow-ups: store card images in Supabase storage instead of proxying them, E2E tests, CI, and rate limiting for MCP tools.
