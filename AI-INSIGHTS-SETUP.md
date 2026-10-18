# AI Match Insights (server-side LLM) — setup

The site now has an **optional** second layer of AI: at data-update time a
GitHub Action asks a language model to write a short, neutral preview for each
upcoming match. The text is saved into `ai-insights.js` and shown inside the
“AI insight” drop-down of the **AI** prediction engine. Your API key stays on
the server (GitHub) and is **never** put in the browser or committed to the
repository.

If you do nothing, the site still works exactly as before: without a key the
insight text falls back to the built-in, in-browser explanation.

## What was added

| File | Purpose |
|------|---------|
| `generate_insights.py` | Runs after `fetch_data.py`. Reads `data.js`, calls an OpenAI-compatible chat model, writes `ai-insights.js` + `ai-insights-cache.json`. Standard library only. |
| `ai-insights.js` | `window.AI_INSIGHTS = { fixtureId: { text, model, generatedAt } }`. Loaded by `index.html`. |
| `ai-insights-cache.json` | Server cache so unchanged matches are **not** re-sent to the model (cost control). |
| `api-config.json` → `aiInsights` | Model, base URL, limits (see below). |
| `.github/workflows/update-data.yml` | New step “Generate LLM match insights” + copies `ai-insights.js` into the published site. |
| `app.js` / `index.html` | Prefer the LLM text when present, otherwise use the built-in text. |

## One-time setup on GitHub

1. Open your repository → **Settings → Secrets and variables → Actions**.
2. Under **Secrets**, click **New repository secret**:
   - Name: `LLM_API_KEY`
   - Value: your model provider key (e.g. an OpenAI key `sk-...`).
3. (Optional) Under **Variables**, you may add:
   - `LLM_BASE_URL` — e.g. `https://api.openai.com/v1` (default),
     `https://openrouter.ai/api/v1`, `https://api.groq.com/openai/v1`, etc.
   - `LLM_MODEL` — e.g. `gpt-4o-mini` (default), `gpt-4.1-mini`, or any model
     your provider exposes.

That is all. The next scheduled run (or a manual **Actions → Run workflow**)
will generate the insights and deploy them.

> If you skip step 2, the workflow still runs green — it just prints
> “AI insights step skipped (no LLM_API_KEY)” and the site uses its built-in
> insight text.

## Tuning (`api-config.json` → `aiInsights`)

```json
"aiInsights": {
  "enabled": true,              // master switch
  "baseUrl": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "temperature": 0.4,
  "maxTokens": 160,
  "timeoutSeconds": 40,
  "daysAhead": 4,               // only matches kicking off within N days
  "maxFixturesPerRun": 60,      // hard cap on model calls per run (cost control)
  "requestSpacingSeconds": 0.4  // gentle pacing between calls
}
```

`LLM_BASE_URL` / `LLM_MODEL` environment variables (GitHub **Variables**)
override `baseUrl` / `model` from the config, so you can switch provider
without editing the repo.

## How cost is controlled

- Only **upcoming** matches (status `NS`) within `daysAhead` are considered.
- Each insight is cached against a hash of its input numbers. On the next run,
  a match whose probabilities/odds have not meaningfully changed is **reused
  for free** — no new model call.
- `maxFixturesPerRun` caps how many new/changed matches are sent each run.
- Expired entries (kick-off more than 7 days ago) are pruned automatically.

## Safety / correctness notes

- The model is told to use **only** the supplied numbers, to write 2 neutral
  sentences, and to give **no betting advice and no guarantees**. All figures,
  picks, confidence and value flags on the site are still computed by the
  site’s own models — the LLM only writes the narrative sentence.
- A secret-leak guard refuses to publish if the API key ever appears in the
  output file.
- The insight step never fails the deploy: any provider/network error is
  logged and skipped, keeping previously cached text.
- These remain **model estimates, not betting advice**. Please keep the
  responsible-gambling messaging on the site.
