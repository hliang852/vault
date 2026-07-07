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

**Status: overlapping clustering built (2026-07-06).** Weighted similarity scoring and the top-4-nearest-neighbor trimmed graph were pre-existing; this session added the multi-membership clustering layer plus 7 new weighted features (see `Architecture.md` for the full detail, weights, and rarity numbers).

**What was actually built:**
- **Axis tags (`src/cluster/axes.py`, primary clustering mechanism).** 7 rule-based, hand-defined descriptive dimensions per case (consent, price-discovery type, regulatory friction, precedent-value text, instigator identity, lock-up signal count, activist signature) -- ported from the notebook's Lenses 1/2/3/4/5/6/8. A case naturally carries several axis values simultaneously, satisfying `Claude.md`'s overlapping/multi-membership requirement. These are the intended basis for the scenario-playbook UI's cluster groupings -- **not yet consumed by any UI** (that's Part 3, still planned below).
- **k-clique community detection (secondary/diagnostic cross-check, not primary).** A full untrimmed pairwise graph at `MIN_SCORE=1.5`, `networkx.algorithms.community.k_clique_communities(k=3)`. On the current 62-case corpus this is **degenerate** (1 community containing all 62 nodes) -- flagged in `To-do.md` as needing parameter tuning, not silently changed.
- **7 new weighted features** added to `pair_score()`'s `BOOLEAN_FEATURES`, each weight grounded in the feature's real true-rate in the corpus (`price_was_bumped_bool`, `multi_jurisdiction`, `toehold_present_flag`, `notes_flags_precedent_setting`, and the three `timeline_post_*` columns). See `Architecture.md` for the table.
- **`short_name`** per node (compact display label; feeds the Part 3 viewer fix below).

**Still not built / open:**
- A UI that actually reads the axis tags / community IDs and renders them as browsable overlapping clusters with a scenario-playbook view -- this session built the underlying data layer (`axes`, `community_ids`, `communities` in `output/precedent_graph_data.json`) but no viewer surface for it yet. That's Part 3 scope, see below.
- Tune `K_CLIQUE`/the community-detection `MIN_SCORE` given the degenerate result above.
- Review the *pre-existing* hand-set weights (`CATEGORICAL_FEATURES`, `ACTIVIST_MATCH_WEIGHT`) against `src/explore.py` / `notebooks/exploratory_analysis.py`'s rarity and coverage diagnostics -- not done this session, still open.
- Decide whether `TOP_K` (4) and `MIN_SCORE` (1.5) still produce a legible, useful viewer graph as more cases or features are added.
- No decisions have been made yet on changing spatial-layout logic (currently D3's force simulation, unmodified) -- any change here is Part 3 scope, tracked below.

## Part 3 -- Interactive viewer & report generation

**Status: one small label fix this session (2026-07-06); scenario-playbook UI and report generation do not exist yet.**

`viewer/Japan_Precedent_Constellation.html` already renders the Part 2 graph with Explore and Find-Precedent modes (see `Architecture.md`). This session changed only the on-circle node label from `d.id` to `d.short_name`.

**Planned, not yet done:**
- **The scenario-playbook UI itself** -- per `Claude.md`'s product vision, browsing a cluster (from the axis tags built in Part 2 this session) and seeing a descriptive breakdown of what happened across its precedents (resolution mechanisms, outcome mix, regulatory/timeline friction, recurring debate points). Part 2 this session produced the underlying data (`axes`, `community_ids`, `communities` in the output JSON) but **no UI reads or displays any of it yet** -- this is still fully open.
- A build step that regenerates the viewer's embedded `DATA` object from `output/precedent_graph_data.json` automatically, replacing today's manual copy-paste (tracked as an open item in `To-do.md`).
- Report generation -- no such feature exists yet. Needs scoping: format (PDF/Markdown/HTML), what a "report" contains (single-case brief? cross-case comparison? both?), and whether it's generated from the viewer or as a separate script.
- Any changes to node/edge visual encoding, spatial layout, or filtering beyond what's already built.
