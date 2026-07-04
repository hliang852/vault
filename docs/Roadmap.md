# Roadmap

Three-part plan for this project. Status reflects what has actually been built, not aspirations -- see `Changelog.md` for the dated history behind each status.

## Part 1 -- Data exploration & visualization

**Status: built (2026-07-04).**

- `src/explore.py` produces a data-quality report (`output/reports/data_quality.md`) and a set of charts (`output/figures/`) directly from `data/Japan.csv`.
- Adaptive to schema changes via column-discovery-by-naming-convention -- see `Architecture.md` for the mechanism.
- Not yet done: nothing planned beyond what's built is currently scoped for Part 1. Extend the anchor-column list or add new dynamic-discovery groups only if a new naming convention is introduced in the data.

## Part 2 -- Clustering / similarity weights

**Status: pre-existing, not modified this session.**

`src/cluster/precedent_engine.py` already implements a rule-based, weighted pairwise similarity score and a top-4-nearest-neighbor trimmed graph (see `Architecture.md` for the current weights and trimming rule). This session only fixed its file paths after moving it into `src/cluster/`.

**Planned, not yet done:**
- Review the current hand-set weights (`CATEGORICAL_FEATURES`, `BOOLEAN_FEATURES`, `ACTIVIST_MATCH_WEIGHT` in `precedent_engine.py`) against what `src/explore.py`'s data-quality report and charts reveal (e.g. field coverage, distribution skew) before adjusting them.
- Decide whether `TOP_K` (4) and `MIN_SCORE` (1.5) still produce a legible, useful graph as more cases or features are added.
- No decisions have been made yet on changing spatial-layout logic (currently D3's force simulation, unmodified) -- any change here is Part 3 scope, tracked below.

## Part 3 -- Interactive viewer & report generation

**Status: viewer pre-existing, not modified this session (moved only). Report generation does not exist yet.**

`viewer/Japan_Precedent_Constellation.html` already renders the Part 2 graph with Explore and Find-Precedent modes (see `Architecture.md`).

**Planned, not yet done:**
- A build step that regenerates the viewer's embedded `DATA` object from `output/precedent_graph_data.json` automatically, replacing today's manual copy-paste (tracked as an open item in `To-do.md`).
- Report generation -- no such feature exists yet. Needs scoping: format (PDF/Markdown/HTML), what a "report" contains (single-case brief? cross-case comparison? both?), and whether it's generated from the viewer or as a separate script.
- Any changes to node/edge visual encoding, spatial layout, or filtering beyond what's already built.
