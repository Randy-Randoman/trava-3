# External services setup

Trava needs three things beyond Supabase: an LLM provider, a web search API, and (implicitly) Playwright for scraping. Here's how to get each.

## LLM provider — pick one

Set `LLM_PROVIDER` to `google` or `anthropic` in `.env`, then fill in the matching key.

### Gemini (recommended default — free tier)

1. Go to [aistudio.google.com](https://aistudio.google.com).
2. Click **Get API key**.
3. Paste into `.env` as `GOOGLE_API_KEY`.
4. Set `LLM_PROVIDER=google`.

### Claude

1. Go to [console.anthropic.com](https://console.anthropic.com).
2. Create an API key under **API keys**.
3. Paste into `.env` as `ANTHROPIC_API_KEY`.
4. Set `LLM_PROVIDER=anthropic`.
5. Note: Anthropic doesn't have a perpetual free tier — you'll need credits.

## Tavily — web and image search

Used by the `web_search` skill for hotel descriptions, activities, and card images.

1. Sign up at [tavily.com](https://tavily.com).
2. Copy your API key from the dashboard.
3. Paste into `.env` as `TAVILY_API_KEY`.

The free tier gives 1,000 searches/month, which is plenty for local development.

## Playwright — Booking.com scraping

Used by the `booking` skill to pull real hotel prices. No account needed — it runs a local Chromium browser.

```bash
cd backend
source .venv/bin/activate
playwright install chromium
```

Do this once, after `pip install -r requirements.txt`. The browser binary is ~200 MB.

## Troubleshooting

- **"Search failed: Playwright/Chromium may not be installed."** — run `playwright install chromium` in the backend venv.
- **"Failed to generate response from LLM."** — check that `LLM_PROVIDER` matches the key you set, and that the key has quota remaining.
- **Empty chat responses** — check the backend terminal for exceptions. Most commonly a missing / wrong env var.
