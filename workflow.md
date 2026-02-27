# Development Workflow with Claude Code

## Overview

This is the standard development workflow used across projects. It defines how projects are structured, how work is tracked, and how Claude Code is guided through a project lifecycle.

---

## Project Files

Every project contains these core files:

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Instructions for Claude Code — how we work, key commands, principles |
| `idea.md` | Brainstorm and describe the overall idea collaboratively with Claude |
| `plan.md` | Break the idea into a concrete, phased implementation plan |
| `learning.md` | Document learnings from coding and debugging as they happen |

### `CLAUDE.md` — The Rulebook

This is the first file Claude Code reads. It contains:

- **How we work**: reference to `idea.md`, `plan.md`, `learning.md` and their purpose
- **Work tracking**: we use GitHub Issues for progress, grouped by phase
- **Key commands**: how to start the app, run tests, build, deploy
- **Coding principles**:
  - Tests for all code we produce
  - No overengineering
  - Good coding principles (clean, simple, readable)
- **Update cycle**: `plan.md` gets updated after each phase is completed

### `idea.md` — The Vision

- Created at the start of a project
- Used to brainstorm and refine the idea **together** with Claude
- Captures the what and why — scope, tools, decisions, open questions
- Living document — updated as decisions are made

### `plan.md` — The Execution Plan

- Derived from `idea.md`
- Breaks the idea into **phases** with concrete steps
- Each phase gets split into **GitHub Issues**
- Updated after each phase is completed (reflect what was done, adjust next phases)

### `learning.md` — The Knowledge Base

- Filled during development, not upfront
- Captures learnings from coding, debugging, and problem-solving
- Prevents repeating mistakes
- Useful reference for similar future projects

---

## Workflow Steps

```
1. CLAUDE.md    → Set up the rules and context
2. idea.md      → Brainstorm the idea with Claude
3. plan.md      → Turn the idea into a phased plan
4. GitHub Issues → Split plan phases into trackable issues
5. Review       → User reviews the issues
6. Execute      → Clear context, start Agent to orchestrate work
7. learning.md  → Document learnings as they come up
8. Repeat       → Update plan.md after each phase, continue
```

### Step by Step

1. **Create `CLAUDE.md`** — Define how we work, key commands, coding principles
2. **Create `idea.md`** — Describe the idea, brainstorm with Claude, make decisions
3. **Create `plan.md`** — Structure the idea into phases and concrete steps
4. **Split into GitHub Issues** — Each phase becomes a group of issues
5. **Review issues** — User reviews the created issues for correctness and completeness
6. **Clear context & start Agent** — Fresh context, Agent reads issues and orchestrates:
   - Uses **sub-agents to work on issues in parallel** where possible
   - **Tests and verifies** results end-to-end
   - **Asks the user** to handle things it can't do (manual steps, browser auth, external config)
7. **Document in `learning.md`** — Capture learnings during coding/debugging
8. **Update `plan.md`** — After each phase, reflect and adjust the plan for next phases

---

## Principles

- **Tests for everything** — no code without tests
- **No overengineering** — solve the problem at hand, nothing more
- **Clean code** — readable, simple, well-structured
- **Iterative** — plan in phases, adjust as you learn
- **Document as you go** — learnings are captured immediately, not after the fact
