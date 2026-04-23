# Contributing

Thanks for considering a contribution. This is an early single-maintainer project — the bar for getting changes in is pragmatic, not heavyweight.

## Dev setup

See the [Quickstart in the README](README.md#quickstart). You'll need a Supabase project + LLM / Tavily keys of your own.

## Before opening a PR

- **Small PRs** (typo fixes, doc tweaks, tiny bug fixes): go ahead and open one directly.
- **Larger changes** (new skills, architecture shifts, API changes): open an issue first so we can align before you spend time.

## Code style

- Python: match existing style (PEP 8, type hints where they help). No formatter is enforced yet.
- TypeScript: match existing style. No linter blocker; `npm run lint` gives hints.
- Keep it simple. The [project ethos](CLAUDE.md) is "simplicity wins over cleverness."

## Tests

Run the unit suite before pushing:

```bash
source backend/.venv/bin/activate
python -m pytest tests/unit/ -v
```

Non-trivial changes should include at least one test. URL builders, validators, and pure logic are easiest to cover.

## Adding a skill

The fastest way to contribute capability is to add a skill. See the ["Adding a skill" walkthrough](README.md#adding-a-skill) in the README.

## Reporting bugs

Open an issue with: what you did, what happened, what you expected. Include `.env` values only if you're sure they're not sensitive — redact service keys.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
