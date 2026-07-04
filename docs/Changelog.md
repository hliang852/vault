# Changelog

Dated log of changes made to this repo and why. Newest entries first.

## 2026-07-04

- **Reorganized the repo into `data/`, `src/`, `docs/`, `output/`, `viewer/`.** Previously everything lived flat in the working directory. Moving to a conventional layout was a prerequisite for Part 1 (adding a real exploration script) and for making the repo presentable as an open-source project.
- **Added `src/explore.py` (Part 1 -- data exploration & visualization).** Generates a data-quality report and a set of charts directly from `data/Japan.csv`, using column-discovery-by-naming-convention so it keeps working if the CSV's schema changes. See `Architecture.md` for design details.
- **Fixed `src/cluster/precedent_engine.py`'s file paths after the move.** It previously read/wrote `Japan.csv` / `precedent_graph_data.json` relative to the working directory; now resolves `data/Japan.csv` and `output/precedent_graph_data.json` relative to the repo root via `pathlib.Path(__file__)`, so it runs correctly regardless of caller cwd. No scoring/weight logic was changed.
- **Moved `Japan_Precedent_Constellation.html` to `viewer/`.** No content changes -- its graph data is embedded inline in the file, so the move doesn't affect it.
- **Added the 4 running docs** (`Architecture.md`, `Changelog.md`, `To-do.md`, `Roadmap.md`) to track structure decisions, changes, open manual-verification items, and the 3-part roadmap across sessions.
- **Initialized git.** The project previously had no version control.
