# WISAG Strategic Financial Foresight — Co-Pilot Prototype

AI-powered **Contribution Margin Co-Pilot** for the WISAG FUTURY Build Days challenge.
Detects margin deviations, **explains the why** via additive driver decomposition,
and generates decision-ready recommendations using the Claude API.

## What it does

| Page | Purpose |
|---|---|
| Home | Dataset loader, filters, portfolio KPI snapshot |
| Portfolio Overview | Heatmap of CM% by region×month, top cost centers, top-10 anomaly leaderboard |
| Deep Dive | Pick a cost center -> CM timeline + **driver waterfall** + KPI vs regional peers + **AI explanation** |
| Early Warnings | Forward-looking rule-based risk list (declining trend, absence spike, subcontractor creep, renewal risk, plan gap widening) with AI action plans |
| Co-Pilot Chat | Natural-language Q&A over the filtered data slice |

## Project layout

| Directory   | What it is                                                    |
|-------------|---------------------------------------------------------------|
| `src/`      | Analytics pipeline (pandas, scipy, anthropic) + UI helpers    |
| `app.py`    | Streamlit entry point                                         |
| `pages/`    | Streamlit multipage screens (Analytics, Forecasts, …)         |
| `data/`     | Sample datasets                                               |

## Local setup

### Prerequisites

- `Python 3.12+`

### 1. Environment

```bash
python -m venv .venv
source .venv/Scripts/activate   # or .venv\Scripts\activate on cmd
pip install -r requirements.txt
cp .env.example .env
```

Optional:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Run

```bash
streamlit run app.py
```

### 3. Load the provided sample dataset

The app accepts both Excel and CSV files. Drop a file into `data/` and load it
from there, or paste a full path into the data-source field.

CSV loading handles non-UTF-8 encodings like `ISO-8859-1` (required for the
provided challenge dataset).

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
                                   Streamlit (app.py + pages/)
```

- **`src/config.py`** — Excel column-letter → semantic-name map (single source of truth)
- **`src/data_loader.py`** — load, rename, coerce types, build `period`
- **`src/features.py`** — derived KPIs (productivity, absence, subcontractor share, etc.) + MoM/YoY/rolling
- **`src/anomaly.py`** — z-score, MoM jump, regime flip, plan miss — ranked by € impact
- **`src/drivers.py`** — **additive variance decomposition** of ΔCM into revenue + cost drivers; includes residual so we're honest about unexplained effects
- **`src/benchmarks.py`** — historical baseline + regional peer KPI comparison
- **`src/early_warning.py`** — explainable rule set for proactive risk flags
- **`src/llm_copilot.py`** — Claude Sonnet 4.6 wrapper with prompt caching; strict rules (cite € values, never invent, distinguish fact vs hypothesis)
- **`src/viz_svg.py`** — inline-SVG chart helpers (area, waterfall, heatmap, timeline) used by Streamlit

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
