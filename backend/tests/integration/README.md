# Integration tests (local Supabase)

These tests run against a real local Supabase stack and check the database row rules,
the `canvas-images` storage rules, and the main API flow.

```bash
supabase start                      # from the repo root (applies supabase/migrations)
cd backend && python -m pytest tests/integration -v
```

- URL and keys come from `supabase status -o env`. If the stack isn't running, every test is skipped.
- Each run creates two throwaway users (A and B) and deletes them at the end; each test makes its own trips.
- `python -m pytest tests/unit` never collects these tests.
