# Editorial Assistant

A multi-agent editorial pipeline with a human-in-the-loop web UI: scout breaking
news, research it, and draft articles from it — approving or rejecting at each
stage, with an LLM-as-judge quality score alongside every approval.

## Why this project

Most "multi-agent" demos are a fixed sequence of LLM calls wearing an agent
costume. This one draws a real line: `scout_agent` and `synthesis_agent` are
single-shot LLM calls with a role — `research_agent` is an actual agent,
running a multi-turn tool-calling loop where the model itself decides what to
search for, which pages to fetch, and when it has enough to write the brief.
Every stage is also independently scored by an LLM-as-judge on a stage-specific
rubric, and nothing reaches "approved" without a human clicking approve —
the pipeline proposes, it doesn't publish.

## Status

| Stage                                                                | Status      |
| -------------------------------------------------------------------- | ----------- |
| Scout — monitor an RSS feed, score importance, judge quality         | **Working** |
| Research — agentic tool-calling loop (search + fetch), judge quality | **Working** |
| Synthesis — draft an article from a brief, judge quality             | Not built   |
| Offline evaluation suite                                             | Not built   |

## Architecture

```text
scout_agent/  →  research_agent/  →  synthesis_agent/
      \               |                    /
       \              |                   /
        \-------- evaluation/  ----------/
                       |
                  backend/
                       |
                  frontend/
```

- `scout_agent/` — monitors an RSS feed, scores each article's importance in
  one LLM call.
- `research_agent/` — an agentic tool-calling loop; the model decides what to
  `search` for and which URLs to `fetch`, then writes the brief.
- `synthesis_agent/` — drafts an article from a research brief in one LLM
  call.
- `evaluation/` — LLM-as-judge, one rubric per stage.
- `backend/` — FastAPI, Postgres via SQLAlchemy + Alembic.
- `frontend/` — React + Vite.

## Running it locally

```bash
docker compose up -d db
uv sync
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.main:app --port 8000
```

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Copy `.env.example` to `.env` and set a real `OPENAI_API_KEY` (Gemini, via
[AI Studio](https://aistudio.google.com/)) for the scout to actually run, and
a `TAVILY_API_KEY` ([tavily.com](https://tavily.com), free tier) for the
research agent's `search` tool.

## Known limitations

- **No auth.** The API is unauthenticated and single-tenant — deferred for
  the MVP, deliberately.
- **No automated tests yet.** Implementation-first pass; tests are a planned
  follow-up.
- **No search-result caching or rate-limit handling** beyond what Tavily's
  free tier gives you — expect to hit its monthly cap with heavy use.
- **Research trace is captured but not shown.** Every tool call the research
  agent makes is logged incrementally to `research_trace.json`; there's no UI
  panel rendering it yet.
