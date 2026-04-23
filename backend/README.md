# WISAG Financial Co-Pilot — FastAPI backend

Wraps the pandas / scipy analytics in [../src/](../src/) behind a REST + SSE API.
The Next.js frontend under [../web/](../web/) is the sole client.

## Run locally

```bash
# from repo root
python -m venv .venv && source .venv/Scripts/activate     # Windows Git Bash
pip install -r backend/requirements.txt
# optional — enables AI explanations and chat streaming
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn backend.main:app --reload
```

The server listens on `http://localhost:8000`. OpenAPI docs at `/docs`.

## Endpoints

| Method | Path                                                    | Purpose |
|--------|---------------------------------------------------------|---------|
| GET    | `/health`                                               | liveness |
| POST   | `/api/datasets`                                         | load from URL / path / Google Sheets |
| GET    | `/api/datasets/{id}/summary`                            | re-read cached summary + facets |
| GET    | `/api/datasets/{id}/portfolio`                          | KPIs + heatmap + top ccs + top anomalies |
| GET    | `/api/datasets/{id}/deep-dive/{cc_id}?mode=mom|yoy|plan`| timeline, waterfall drivers, peer KPIs |
| GET    | `/api/datasets/{id}/early-warnings`                     | rule-based risk flags |
| GET    | `/api/datasets/{id}/plan-vs-actual`                     | monthly plan-vs-actual table |
| POST   | `/api/datasets/{id}/chat`                               | SSE stream of Claude Q&A |
| POST   | `/api/datasets/{id}/explain`                            | SSE stream of driver explanation |

Filters (`regions`, `services`, `start`, `end`) are accepted as query params on
all GET aggregates and the chat POST.

## Environment

- `ANTHROPIC_API_KEY` — enables Claude; without it the explain endpoint returns
  the template fallback and the chat endpoint returns a single warning delta.
- `ALLOWED_ORIGINS` — comma-separated CORS origins. Defaults to
  `http://localhost:3000` for local dev.

## Docker

```bash
docker build -t wisag-backend -f backend/Dockerfile .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e ALLOWED_ORIGINS=https://your-frontend.vercel.app \
  wisag-backend
```
