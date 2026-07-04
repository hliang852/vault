# Architecture

Describes the **current, built state** of the repo. Planned-but-unbuilt work lives in `Roadmap.md`, not here.

## Repo layout

```
data/     source CSVs (Japan_Master.csv, Japan.csv, Japan_Codebook.csv, Japan_Watchlist.csv, masterfile.xlsx)
src/
  explore.py            Part 1 -- data exploration & visualization
  cluster/
    precedent_engine.py Part 2 -- similarity scoring + graph construction
viewer/
  Japan_Precedent_Constellation.html   Part 3 -- interactive D3 viewer
output/   generated artifacts (gitignored, regenerable from src/ + data/)
docs/     this file set + source methodology docs
```

## Data flow

```
data/Japan.csv
   |
   |-- src/explore.py --------------> output/figures/*.png
   |                                  output/reports/data_quality.md
   |
   `-- src/cluster/precedent_engine.py --> output/precedent_graph_data.json
                                             |
                                             v (currently: manual copy-paste)
                                        viewer/Japan_Precedent_Constellation.html
                                        (const DATA = {...} embedded inline)
```

**Known gap:** the viewer's `DATA` object is hand-embedded JavaScript, not loaded from `output/precedent_graph_data.json` at build or load time. Regenerating the graph today does not automatically update the viewer -- see `Roadmap.md` Part 3.

## Part 1 -- data exploration (`src/explore.py`)

Adaptive-by-construction so it keeps working if `Japan.csv`'s columns change:

- **Column discovery by naming convention**, not a hardcoded column list. Groups are found by prefix/suffix match against the conventions in `docs/Japan_User_Guide.md`:
  - `has_*` -> regulator involvement flags
  - `activist_*` -> named-activist-fund flags
  - `structure_has_*` -> deal-structure mechanism flags
  - `*_is_estimate` -> paired with its value column to compute missingness/estimate rates
  - `*_raw` -> checked for high cardinality (>80% unique) to flag columns that shouldn't be modeled on directly
- **Guarded anchor columns.** A short list (`deal_id`, `date_announced_year`, `category_group`, `industry_group`, `outcome_code`, `verification_confidence_code`, `deal_size_usd_mn`) drives the core charts. Every reference checks `col in df.columns` first; a missing/renamed anchor skips that chart with a warning rather than crashing the run.
- **Configurable path**, not hardcoded: `--input` / `--output-dir` CLI args, both resolved relative to the repo root via `pathlib.Path(__file__)` so behavior doesn't depend on the caller's working directory.

Outputs: per-field missingness/estimate-rate table, verification-confidence breakdown, high-cardinality warnings (`output/reports/data_quality.md`); bar charts for deals/year, category/industry group, outcome, verification confidence, regulator involvement, activist frequency, structure mechanisms (`output/figures/`).

## Part 2 -- similarity scoring & graph (`src/cluster/precedent_engine.py`)

Unchanged this session except for path fixes after the file move (now reads `data/Japan.csv` and writes `output/precedent_graph_data.json`, both resolved relative to the repo root).

- **Node semantics** (as rendered in the viewer): size = `deal_size_usd_mn`; color = `category_group`.
- **Edge semantics**: a weighted feature-match score between every pair of deals (`pair_score` in `precedent_engine.py`) -- shared `category_group`/`industry_group`/board posture/regulators/named activists each add a hand-set weight (see the `CATEGORICAL_FEATURES`, `BOOLEAN_FEATURES`, `ACTIVIST_MATCH_WEIGHT` constants in that file). Weights are a practitioner judgment call, not fitted.
- **Graph trimming**: each node keeps only its top-4 nearest neighbors (`TOP_K = 4`) above a minimum score of `1.5` (`MIN_SCORE`), so the rendered graph stays legible on 62 nodes instead of becoming a complete-graph hairball.
- Edge line thickness / link distance in the viewer scale with the match score (see `viewer/Japan_Precedent_Constellation.html`'s `d3.forceLink(...).distance(...)`).

## Part 3 -- interactive viewer (`viewer/Japan_Precedent_Constellation.html`)

Unchanged this session (moved only). Self-contained D3.js force-directed graph with two modes:

- **Explore mode**: browse the precomputed precedent graph; click a node to see its brief and top precedent links with reasons.
- **Find Precedent mode**: score a hypothetical new deal's facts against all 62 cases using the same weighting scheme.

No report-generation feature exists yet (see `Roadmap.md`).
