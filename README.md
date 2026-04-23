# WISAG Strategic Financial Foresight — Co-Pilot Prototype

AI-powered **Contribution Margin Co-Pilot** for the WISAG FUTURY Build Days challenge.
Detects margin deviations, **explains the why** via additive driver decomposition,
and generates decision-ready recommendations using the Claude API.

## What it does

| Page | Purpose |
|---|---|
| 🏠 Home | Dataset loader, filters, portfolio KPI snapshot |
| 📈 Portfolio Overview | Heatmap of CM% by region×month, top cost centers, top-10 anomaly leaderboard |
| 🔎 Deep Dive | Pick a cost center → CM timeline + **driver waterfall** + KPI vs regional peers + **AI explanation** |
| ⚠️ Early Warnings | Forward-looking rule-based risk list (declining trend, absence spike, subcontractor creep, renewal risk, plan gap widening) with AI action plans |
| 💬 Co-Pilot Chat | Natural-language Q&A over the filtered data slice |

## Two front-ends in this repo

This project ships both the original Streamlit prototype **and** a Next.js
rewrite backed by a FastAPI API over the same analytics modules in `src/`.

| Directory   | What it is                                                    |
|-------------|---------------------------------------------------------------|
| `src/`      | Analytics pipeline (pandas, scipy, anthropic) — shared        |
| `app.py` + `pages/` | Original Streamlit multipage app                      |
| `backend/`  | FastAPI wrapping `src/` as REST + SSE                         |
| `web/`      | Next.js 15 (App Router, TS, Tailwind, react-plotly.js)        |

## Local setup on your machine

### Prerequisites

- `Python 3.12+`
- `Node.js 20+`
- `pnpm` (Corepack works fine: `corepack enable`)

### 1. Backend environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
```

Optional:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Frontend environment

```bash
cd web
pnpm install
cd ..
```

### 3. Run in local development mode

Terminal 1:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

Terminal 2:

```bash
cd web
pnpm dev
```

Open:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

### 4. Run in single-port production-like mode

```bash
cd web && pnpm build && cd ..
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

### 5. Load the provided sample dataset

The app accepts both Excel and CSV files. The supplied CSV in Downloads works:

```text
/Users/uzair99/Downloads/Dataset_anoym(Datensatz für Test (anonym)).csv
```

Paste that full path into the app's data-source field, or move the file into
`data/` and load it from there.

CSV loading now handles non-UTF-8 encodings like `ISO-8859-1`, which was
required for the provided challenge dataset.

### Streamlit (original)

```bash
python -m venv .venv && source .venv/Scripts/activate   # or .venv\Scripts\activate on cmd
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...                     # optional
streamlit run app.py
```

### Next.js + FastAPI (new) — one server

The React UI is built as a static bundle (`web/out/`) and served by FastAPI
alongside the `/api/*` routes. You run **one** process on **one** port.

```bash
# 1. install deps (once)
pip install -r backend/requirements.txt
cd web && pnpm install && pnpm build && cd ..
export ANTHROPIC_API_KEY=sk-ant-...                     # optional

# 2. run everything
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 — landing page, UI, and API all live there.
Paste a Google Sheets URL or use `data/Dataset_anoym.xlsx`.

**Hot-reload dev mode** (two processes, only if you're hacking on the frontend):
```bash
uvicorn backend.main:app --reload                       # :8000
cd web && pnpm dev                                      # :3000 with live reload
```

**Docker**:
```bash
docker compose up   # single `web` service, port 8000
```

Without an `ANTHROPIC_API_KEY` the app still renders every chart and driver —
the chat streams a single warning message and the AI explanation falls back
to a template.

## Architecture

```
Excel / Google Sheets
         │
         ▼
   data_loader ──▶ features ──┬── anomaly ──────┐
                              ├── drivers ──────┤
                              ├── benchmarks ───┼──▶ llm_copilot
                              └── early_warning─┘        │
                                         │               │
                                         ▼               ▼
                           FastAPI (backend/)  OR  Streamlit (app.py)
                                         │
                                         ▼
                                   Next.js (web/)
```

- **`src/config.py`** — Excel column-letter → semantic-name map (single source of truth)
- **`src/data_loader.py`** — load, rename, coerce types, build `period`
- **`src/features.py`** — derived KPIs (productivity, absence, subcontractor share, etc.) + MoM/YoY/rolling
- **`src/anomaly.py`** — z-score, MoM jump, regime flip, plan miss — ranked by € impact
- **`src/drivers.py`** — **additive variance decomposition** of ΔCM into revenue + cost drivers; includes residual so we're honest about unexplained effects
- **`src/benchmarks.py`** — historical baseline + regional peer KPI comparison
- **`src/early_warning.py`** — explainable rule set for proactive risk flags
- **`src/llm_copilot.py`** — Claude Sonnet 4.6 wrapper with prompt caching; strict rules (cite € values, never invent, distinguish fact vs hypothesis)
- **`src/viz.py`** — Plotly helpers (waterfall, heatmap, timeline, KPI-vs-peer bullet)

## How it scores against the rubric

| Criterion | Implementation |
|---|---|
| **Logic of justification** | Driver deltas sum (±residual) to observed ΔCM; the LLM is forced by its system prompt to cite only € values present in the JSON context |
| **Proportionality & Prioritization** | Drivers ranked by \|€ impact\|; anomalies ranked by €; early warnings ranked by severity × €-at-stake |
| **Visualization & Usability** | Streamlit multipage app, clickable, plotly waterfall as the visual centrepiece, sidebar filters persist across pages |
| **Recommendation for action** | LLM output includes concrete actions + a dedicated section "Additional KPIs that would sharpen this diagnosis" (explicit rubric bonus) |

## Demo script (3 minutes)

1. **Portfolio Overview** — point to the red cells in the heatmap and the €-ranked anomaly table. "The system already prioritizes where managers should look."
2. **Deep Dive** — pick the top anomaly. Show the CM timeline, then the driver waterfall: "Look — subcontractor costs alone account for +45k€, labor direct −60k€, the rest is small." Then click *Generate AI explanation*.
3. **Early Warnings** — show the ranked risk table. "These aren't anomalies that already happened — they're the ones about to. Contract X renews in 60 days and its plan gap is widening."
4. **Chat** — type *"Which region has the weakest CM and why?"*. Done.

## Verifying the math

```python
from src.data_loader import load
from src.features import enrich
from src.drivers import decompose, observed_delta

df, _report = load("data/Dataset_anoym.xlsx")
df = enrich(df)
cc = df["cost_center_id"].mode().iloc[0]
hist = df[df["cost_center_id"] == cc].sort_values("period")
current, baseline = hist.iloc[-1], hist.iloc[-2]

drv = decompose(current, baseline)
obs = observed_delta(current, baseline)
modeled = sum(d.delta_eur for d in drv)
print(f"observed={obs:+,.0f}€  modeled={modeled:+,.0f}€  "
      f"residual={obs-modeled:+,.0f}€ ({(obs-modeled)/obs:+.1%})")
```

A small residual (<5% of |ΔCM|) is expected and is surfaced honestly in the waterfall.

## Known limits (honest about the prototype scope)

- Variance decomposition uses a simple delta bridge; a full price×volume×mix bridge per revenue stream would require more plan data than this anonymized sample contains.
- Early-warning rules are deliberately rule-based for explainability. A predictive model layer (gradient-boosted classifier on rolling features) is the natural next step for productionization.
- The LLM grounds in the JSON context we send, but does not execute code. Numeric claims are always reproducible from the same JSON that's displayed in the UI.
