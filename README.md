# Japan Special Situations

A case-based precedent library for Japanese M&A/takeover/activism special situations (2023-2026H1). Built for **qualitative pattern study** -- given a new deal's facts, find comparable historical precedents and see what typically happened. Explicitly not a quantitative trading-signal or predictive model.

## Status

- **Part 1 -- data exploration & visualization: built.** (`src/explore.py`)
- **Part 2 -- similarity scoring & precedent graph: built** (pre-existing, unmodified this session; see `docs/Architecture.md`). (`src/cluster/precedent_engine.py`)
- **Part 3 -- interactive viewer: built** (pre-existing, unmodified this session); **report generation: not yet built.** (`viewer/Japan_Precedent_Constellation.html`)

See `docs/Roadmap.md` for what's planned next, `docs/Architecture.md` for how the current graph/viz encoding works, and `docs/Changelog.md` for the dated history of changes.

## Repo layout

```
data/     source CSVs
src/      Python: explore.py (Part 1), cluster/precedent_engine.py (Part 2)
viewer/   interactive HTML viewer (Part 3)
output/   generated figures/reports/graph data (gitignored, regenerable)
docs/     architecture, changelog, to-do, roadmap, and source data documentation
```

## Running it

```
pip install -r requirements.txt
python src/explore.py                    # data exploration + charts -> output/
python src/cluster/precedent_engine.py   # precedent graph -> output/precedent_graph_data.json
open viewer/Japan_Precedent_Constellation.html
```

## Data

`data/Japan.csv` is a machine-learning-ready recoding of the hand-curated `data/Japan_Master.csv` masterfile. See `docs/Japan_User_Guide.md` for the full field dictionary and `docs/Japan_README.md` for source methodology and known limitations -- in particular, many prices/premiums/dates are flagged as estimates and should not be treated as verified facts (see `docs/To-do.md` for the open verification backlog).
