# Issue tracker

Agent-facing notes on where work items live and how to handle them.

- **Tracker:** GitHub Issues on `Randy-Randoman/trava-3`, used through the `gh` CLI.
- **Ready for an agent:** label `ready-for-agent`. Pull the queue with
  `gh issue list --label ready-for-agent --state open --json number,title,labels,body`.
- **Phase labels:** `phase-N` matches the phase in [`docs/plan.md`](../plan.md), which is the source of truth for scope and decisions.
- **Dependencies:** every issue ends with a `## Blocked by` section. Never start an issue before its blockers are closed or merged into the integration branch.
- **Solo-phase hints:** labels `database` (migrations) and `dependencies` (package upgrades).
- **Integration branch:** `dev`. Never commit to `main`; `dev` → `main` goes through one PR per phase.
- **Tests:**
  - Backend unit: `cd backend && python -m pytest tests/unit -q`
  - Backend integration (needs `supabase start`): `cd backend && python -m pytest tests/integration -q`
  - Frontend: `cd frontend && npm test && npm run lint && npx tsc --noEmit`
  - Until #42 lands, the backend tests still run from the repo root: `python -m pytest tests/unit -q`
- **Closing:** reference the issue in the commit message (`Closes #N`); the PR to `main` closes it.
- **Not for agents:** steps listed under "Manual steps" in `docs/plan.md` (Supabase dashboard, GitHub settings, live database).
