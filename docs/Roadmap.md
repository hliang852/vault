# Roadmap

Three-part plan for this project. Status reflects what has actually been built, not aspirations -- see `Changelog.md` for the dated history behind each status.

## Part 1 -- Data exploration & visualization

**Status: built (2026-07-04).**

- `src/explore.py` produces a data-quality report (`output/reports/data_quality.md`) and a set of charts (`output/figures/`) directly from `data/Japan.csv`.
- Adaptive to schema changes via column-discovery-by-naming-convention -- see `Architecture.md` for the mechanism.
- `notebooks/exploratory_analysis.py` (added 2026-07-04, Colab-openable) goes deeper, specifically to inform Part 2's similarity/clustering design rather than to model outcomes: data-quality recap, descriptive outcome cross-tabs, feature discriminativeness/rarity, feature co-occurrence/redundancy, pairwise feature-comparability coverage, diagnostics on the existing similarity graph, and seven interpretive "lenses" on the corpus (consent, price-discovery, regulatory friction, precedent-value, instigator-identity, deal-certainty, activist-signature -- see `Architecture.md` for the full list and definitions).
  - **Tried and rejected:** a ninth lens attempted to mine `notes_raw`/`key_debate_points_raw` for explicit cross-case citations (a literal precedent-citation network). Token-matching on company names produced mostly false positives from generic conglomerate-name prefixes (`Japan`, `Nippon`, `Fuji`, `Sumitomo`) and repeat-sponsor overlap (`Bain`, `KKR`, `JIC`) rather than genuine narrative cross-references, so it was dropped rather than shipped as a misleading result. Revisit only with a materially better matching approach.
- Not yet done: nothing else planned beyond what's built is currently scoped for Part 1. Extend the anchor-column list or add new dynamic-discovery groups only if a new naming convention is introduced in the data.

## Part 2 -- Clustering / similarity weights

**Status: pre-existing, not modified this session.**

`src/cluster/precedent_engine.py` already implements a rule-based, weighted pairwise similarity score and a top-4-nearest-neighbor trimmed graph (see `Architecture.md` for the current weights and trimming rule). This session only fixed its file paths after moving it into `src/cluster/`.

**Product vision (see `Claude.md`), not yet built:** the tool should support querying with a new deal's facts, retrieving comparable precedents, grouping them into **overlapping clusters** (a case can belong to more than one -- clustering here is soft, not a hard partition), and displaying a descriptive "scenario playbook" per cluster (what actually happened across that cluster's precedents -- resolution mechanisms, outcome mix, regulatory/timeline friction -- never a predictive probability for the new deal). The current engine produces a single flat nearest-neighbor graph with no cluster labels or multi-membership -- this is a real redesign, not an extension.

**Planned, not yet done:**
- Design overlapping/multi-membership clustering (the core Part 2 redesign described above).
- Review the current hand-set weights (`CATEGORICAL_FEATURES`, `BOOLEAN_FEATURES`, `ACTIVIST_MATCH_WEIGHT` in `precedent_engine.py`) against what `src/explore.py` and `notebooks/exploratory_analysis.py` reveal -- in particular the feature-rarity table (Section 3), the co-occurrence/redundancy check (Section 4, flags features that may be double-counting the same signal), and the pairwise-comparability coverage table (Section 5, flags features whose weight is currently close to moot because both sides of a pair are rarely populated simultaneously).
- Decide whether `TOP_K` (4) and `MIN_SCORE` (1.5) still produce a legible, useful graph as more cases or features are added, informed by the degree-distribution/hub-node diagnostics in Section 6 of the notebook.
- Decide how the seven interpretive lenses (consent, price-discovery, regulatory friction, precedent-value, instigator-identity, deal-certainty, activist-signature) map onto cluster definitions, if at all.
- No decisions have been made yet on changing spatial-layout logic (currently D3's force simulation, unmodified) -- any change here is Part 3 scope, tracked below.

## Part 3 -- Interactive viewer & report generation

**Status: viewer pre-existing, not modified this session (moved only). Report generation does not exist yet.**

`viewer/Japan_Precedent_Constellation.html` already renders the Part 2 graph with Explore and Find-Precedent modes (see `Architecture.md`).

**Planned, not yet done:**
- A build step that regenerates the viewer's embedded `DATA` object from `output/precedent_graph_data.json` automatically, replacing today's manual copy-paste (tracked as an open item in `To-do.md`).
- Report generation -- no such feature exists yet. Needs scoping: format (PDF/Markdown/HTML), what a "report" contains (single-case brief? cross-case comparison? both?), and whether it's generated from the viewer or as a separate script.
- Any changes to node/edge visual encoding, spatial layout, or filtering beyond what's already built.
