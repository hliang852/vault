# Architecture

Describes the **current, built state** of the repo. Planned-but-unbuilt work lives in `Roadmap.md`, not here.

## Repo layout

```
data/     source CSVs (Japan_Master.csv, Japan.csv, Japan_Codebook.csv, Japan_Watchlist.csv, masterfile.xlsx)
src/
  explore.py            Part 1 -- data exploration & visualization
  cluster/
    precedent_engine.py Part 2 -- similarity scoring + graph construction + community detection
    axes.py              Part 2 -- descriptive "axis tag" clustering layer + Jaccard co-occurrence helper
notebooks/
  exploratory_analysis.py   Part 1 -- deeper, Colab-openable exploration feeding Part 2's design
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
  - `timeline_post_*` -> regulatory-timeline overlay flags (added 2026-07-06, see below). Deliberately a distinct prefix from `has_*` so `discover_prefixed_group(df, 'has_')` doesn't sweep these into the regulator-involvement chart -- they're a timing signal, not a regulator-involvement signal.
- **Guarded anchor columns.** A short list (`deal_id`, `date_announced_year`, `category_group`, `industry_group`, `outcome_code`, `verification_confidence_code`, `deal_size_usd_mn`) drives the core charts. Every reference checks `col in df.columns` first; a missing/renamed anchor skips that chart with a warning rather than crashing the run.
- **Configurable path**, not hardcoded: `--input` / `--output-dir` CLI args, both resolved relative to the repo root via `pathlib.Path(__file__)` so behavior doesn't depend on the caller's working directory.

Outputs: per-field missingness/estimate-rate table, verification-confidence breakdown, high-cardinality warnings (`output/reports/data_quality.md`); bar charts for deals/year, category/industry group, outcome, verification confidence, regulator involvement, activist frequency, structure mechanisms (`output/figures/`).

## Part 1 -- deeper exploration (`notebooks/exploratory_analysis.py`)

A single `# %%`-cell-delimited Python file (opens directly in Colab as a notebook; also runs as a plain script). Purpose: characterize the corpus and the inputs to `precedent_engine.py`'s similarity score, to inform Part 2's design -- **diagnostic, not a predictive model** (see `Claude.md`'s "not a quant/ML training set" rule). Duplicates a few small helpers (`blank()`, `discover_prefixed_group()`) from `src/explore.py`/`src/cluster/precedent_engine.py` rather than importing them, so the notebook stays a single portable file that runs in a fresh Colab session with no repo cloned.

Sections, in order:

1. **Data quality recap** -- condensed inline version of `output/reports/data_quality.md`'s logic.
2. **Outcome distribution & cross-tabs** -- descriptive context, not a success model. Convention used throughout: a "conclusion rate" is always `Concluded / (Concluded + Failed)`, with `Other/Unclear` rows shown as their own count/column and never folded into either side (the corpus-wide `Other/Unclear` %, plus 3 examples, is reported once in Section 1). Every cross-tab shows raw counts alongside any rate, and flags any group with n < 10 -- no significance testing is performed anywhere (n=62, hand-picked, non-random corpus; see `Claude.md`).
3. **Feature discriminativeness / rarity** -- for every feature `precedent_engine.py` scores on, how rare vs. common is it (e.g. `has_CFIUS` true in 2/62 vs. `has_JFTC` true in 39/62). Empirical basis for checking whether the engine's hand-set weights track rarity as its own design logic claims.
4. **Feature co-occurrence / redundancy** -- Jaccard similarity between boolean flags (min. support 3 rows), to flag pairs that may be double-counting one underlying signal if both are weighted independently.
5. **Pairwise comparability coverage** -- `precedent_engine.py` only scores a feature match when both rows in a pair are non-blank on it. Boolean flags (`has_*`/`structure_has_*`/`activist_*`) default to `False` so their coverage is always 100%; the categorical features (`board_recommendation_code`, `competing_bid_flag`, `squeeze_out_mechanism_code`, etc.) are where coverage actually degrades -- as low as ~28% of all pairs for `competing_bid_flag` at last check.
6. **Existing similarity-graph diagnostics** -- loads the already-generated `output/precedent_graph_data.json` (no engine changes) and reports degree distribution, hub nodes, and the edge-score histogram relative to `MIN_SCORE`.
7. **Seven interpretive lenses** -- re-framings of existing columns as analytical axes, each grounded in already-existing fields (no new facts):
   - **Lens 1, consent** -- `board_recommendation_code` (For -> Engaged/Mixed -> Opposed).
   - **Lens 2, price-discovery** -- `price_was_bumped` x `board_recommendation_code` x `competing_bid_flag` x `structure_has_MBO`.
   - **Lens 3, regulatory friction** -- `num_regulators` (>=2 = multi-jurisdiction) x `category_group`.
   - **Lens 4, precedent-value** -- full `notes_raw`/`key_debate_points_raw` text, plus a mechanical keyword flag (`notes_flags_precedent_setting`, matching "first"/"template"/"precedent"/"proof-of-concept"/"landmark"/"signature") -- no generated summarization.
   - **Lens 5, instigator-identity** -- derived `instigator_type` (Activist-instigated / Sponsor-instigated / Strategic-instigated) from `category_group`, `has_activist_involvement`, `acquirer_is_unlisted`.
   - **Lens 6, deal-certainty** -- derived `lockup_signal_count` (0-3) from `toehold_present_flag`, `special_committee_flag`, `recurring_acquirer_flag`.
   - **Lens 8, activist signature** -- derived `activist_signature` (sorted list of co-occurring named funds per case), extending Section 4's co-occurrence view to activists specifically.

   (Lens numbering follows the original brainstorm and intentionally skips 7/9/11, which were considered and not carried forward.)

**Tried and rejected:** a precedent-citation-network lens (mining `notes_raw`/`key_debate_points_raw` for explicit mentions of other cases' company names) was attempted and dropped -- see `Roadmap.md` Part 1 for why.

## `Japan.csv` schema changes

- **2026-07-06 -- regulatory-timeline overlay.** Added `timeline_post_meti_2023_guideline`, `timeline_post_tse_reform_2023`, `timeline_post_fiea_2026_amendment` (boolean, 131 columns total now vs. 128 before). Each is a mechanical comparison of `date_announced` against a rule's real-world effective date (METI Corporate Takeover Guidelines 2023-08-31; TSE cost-of-capital/PBR reform request 2023-03-31; FIEA mandatory-TOB amendment 2026-05-01) -- no new facts introduced, consistent with `Claude.md`'s parsing discipline. Distinct from the pre-existing `mentions_METI_guidelines`/`mentions_TSE_reform`/`mentions_FIEA` columns, which are keyword flags on whether a deal's regulatory-narrative text happens to *mention* these regimes -- the two are not mutually exclusive or redundant. See `docs/Japan_User_Guide.md`'s Regulatory section for the column description and `docs/Regulatory_Timeline_Appendix.md` for the substantive background on each rule change (what it is, what changed, sourced links). Not yet consumed by `precedent_engine.py` or the viewer -- these are descriptive/filterable columns only, not (yet) part of the similarity-score feature set; adding them as weighted features is a Part 2 decision, not made here.
- **2026-07-06 -- advisor data (pilot batch).** Added `Financial Advisor - Target` / `Financial Advisor - Acquirer` / `Target IPO Advisor` to `data/Japan_Master.csv` (all 62 rows, default `TBV`), then propagated as `financial_advisor_target_raw` / `financial_advisor_acquirer_raw` / `target_ipo_advisor_raw` to `data/Japan.csv` (now 134 columns). This is a deliberate, one-time exception to the "no new facts" discipline in `Claude.md` -- unlike every other column, these are freshly researched from public tender-offer filings and press releases, not parsed from an existing master-file cell. The maintainer decided the exception belongs at the master-file level (research goes into `Japan_Master.csv` first, `Japan.csv` still mechanically derives from it) rather than bolted onto `Japan.csv` directly, to preserve the audit trail. Only a pilot batch of 7 deals (`JP-001, 002, 006, 009, 010, 011` for financial advisors; zero for IPO advisor) were researched and verified before pausing to check in with the maintainer -- see `To-do.md` for what's outstanding and the IPO-advisor sourcing problem encountered. `JP-001` (Toshiba/JIP) was cross-checked against the actual EDINET tender offer statement after web search summaries turned out to materially conflict with each other, which is why that row's advisor text is unusually detailed (distinguishes management-team advisors from the independent Special Committee's advisor).
- **Decided not to add a `situation_id` linking field** (see `To-do.md`/`Roadmap.md` history) for grouping multi-bid contests (e.g. Seven & i/Couche-Tard vs. York/Bain). Each approach/bid stays its own row/node, and the pre-existing `recurring_acquirer_flag` (see `Japan_User_Guide.md`) is the intended signal for "this deal is a repeat/serial approach" -- no new column needed.
- **2026-07-06 -- Part 2 weighting pass.** Added `multi_jurisdiction`, `notes_flags_precedent_setting`, `price_was_bumped_bool` (boolean, 137 columns total now vs. 134 before). All three mechanically derived (no new facts): `multi_jurisdiction` = `num_regulators >= 2`; `notes_flags_precedent_setting` = keyword match on `notes_raw` ("first"/"template"/"precedent"/"proof-of-concept"/"landmark"/"signature"); `price_was_bumped_bool` = a clean boolean fix for the mixed-type source `price_was_bumped` column (`True` only where the source is the literal string `'True'`, correcting a bug the existing `bool(value)` scoring pattern would have caused -- see `Japan_User_Guide.md`). Unlike the `timeline_post_*` columns, these three were added specifically to be scored features in `precedent_engine.py` -- see the weighted-features table below.
- **2026-07-07 -- Part 2 redundancy consolidation.** Added `has_dual_antitrust_review`, `timeline_post_2023_reforms` (boolean, 139 columns total now vs. 137 before). Both are mechanical `AND` combinations of pre-existing columns (no new facts), added after an empirical lift-over-independence review of the full scored feature set found real vs. base-rate-only correlation among several flagged high-Jaccard pairs -- see `Japan_User_Guide.md` for each column's definition and `To-do.md`/`Changelog.md` (2026-07-07) for the full investigation and numbers.

## Part 2 -- similarity scoring & graph (`src/cluster/precedent_engine.py`)

**Extended 2026-07-06** with 7 new weighted features, an axis-tag descriptive clustering layer, a secondary community-detection cross-check, and a `short_name` field. **Further tuned 2026-07-07** to fix a degenerate community-detection result and consolidate 2 pairs of redundant/correlated features (see below and `docs/To-do.md`/`docs/Changelog.md` for the full investigation). The top-4-nearest-neighbor edge graph, its trimming rule (`MIN_SCORE=1.5`), and all pre-2026-07-06 weights are otherwise unchanged.

- **Node semantics** (as rendered in the viewer): size = `deal_size_usd_mn`; color = `category_group`; on-circle label = `short_name` (see below; was `deal_id` before 2026-07-06).
- **Edge semantics**: a weighted feature-match score between every pair of deals (`pair_score` in `precedent_engine.py`) -- shared `category_group`/`industry_group`/board posture/regulators/named activists each add a hand-set weight (see the `CATEGORICAL_FEATURES`, `BOOLEAN_FEATURES`, `ACTIVIST_MATCH_WEIGHT` constants in that file). Weights are a practitioner judgment call, not fitted.
- **Graph trimming**: each node keeps only its top-4 nearest neighbors (`TOP_K = 4`) above a minimum score of `1.5` (`MIN_SCORE`), so the rendered graph stays legible on 62 nodes instead of becoming a complete-graph hairball. This threshold is used only for the viewer's top-4 trim -- community detection below uses its own, separate threshold.
- Edge line thickness / link distance in the viewer scale with the match score (see `viewer/Japan_Precedent_Constellation.html`'s `d3.forceLink(...).distance(...)`).

### Weighted features (added 2026-07-06, 2 pairs consolidated 2026-07-07)

Added to `BOOLEAN_FEATURES`, weight grounded in the feature's actual true-rate in the 62-row corpus (checked empirically before setting the weight, per `Claude.md`'s "not fitted, but not guessed either" convention):

| Feature | True rate (n=62) | Weight | Why |
|---|---|---|---|
| `price_was_bumped_bool` | 7/62 (11%) | 1.0 | Rare and a meaningfully distinct price-discovery signal (clean boolean fixing a real bug -- see `Japan_User_Guide.md`) |
| `multi_jurisdiction` | 29/62 (47%) | 0.5 | Moderately common (`num_regulators>=2`), so a moderate weight |
| `toehold_present_flag` | 44/62 (71%) | 0.25 | Pre-existing column, common -> light weight when shared |
| `notes_flags_precedent_setting` | 7/62 (11%) | 0.5 | Rare but a soft/subjective keyword-derived text flag, so kept modest rather than as strong as a hard structural fact |
| `timeline_post_fiea_2026_amendment` | 0/62 (0%) | 0.1 | Contributes 0 to every score today since the FIEA amendment takes effect 2026-05-01, after this corpus's cutoff; will start mattering once the corpus includes deals announced after that date. Reviewed 2026-07-07, no action -- agreed to leave as-is |
| `has_dual_antitrust_review` | 39/62 (63%) | 0.5 | **Consolidated 2026-07-07**, replacing separately-scored `has_JFTC` (0.1) + `has_DOJ_FTC_HSR` (1.0). An empirical lift analysis (observed co-occurrence vs. expected if independent) found these correlate 1.37-1.54x above base rate -- a real relationship, not a base-rate artifact -- and `has_JFTC`'s true set was an exact subset of `has_DOJ_FTC_HSR`'s in this corpus. Defined as both true. `structure_has_TOB` (0.5) was deliberately left separate and unconsolidated -- it's a distinct deal-structure fact, even though it also correlates with these two (0.80 Jaccard, 1.37-1.54x lift). |
| `timeline_post_2023_reforms` | 53/62 (85%) | 0.1 | **Consolidated 2026-07-07**, replacing separately-scored `timeline_post_meti_2023_guideline` + `timeline_post_tse_reform_2023` (0.1 each). Despite the highest raw Jaccard of any flagged pair (0.93), the lift was only ~1.09x -- almost entirely a base-rate artifact of both being common (85%/92% true), not genuine redundancy. Consolidated anyway per an explicit maintainer caution call, not because the statistical case demanded it. Defined as both true (== `timeline_post_meti_2023_guideline` alone, since it was the subset). |

`has_JFTC`, `has_DOJ_FTC_HSR`, `timeline_post_meti_2023_guideline`, and `timeline_post_tse_reform_2023` remain in `data/Japan.csv` as individual descriptive columns -- only their contribution to `pair_score` was consolidated, so they no longer appear in a node's `features` dict (which mirrors `BOOLEAN_FEATURES` exactly).

`instigator_type`, `lockup_signal_count`, and `activist_signature` (see axes below) are deliberately **not** added as scored features -- each is a pure recombination of columns already independently scored elsewhere (`category_group`, `has_activist_involvement`, `acquirer_is_unlisted`, `toehold_present_flag`, `special_committee_flag`, `recurring_acquirer_flag`, the activist-match mechanism), so scoring the composite too would double/triple-count the same underlying fact. See the code comment in `precedent_engine.py` above `BOOLEAN_FEATURES`.

### Axis tags (`src/cluster/axes.py`) -- the primary multi-membership clustering layer

Per `Claude.md`'s product vision (a case can belong to more than one cluster), each node's `axes` field is a dict of 7 descriptive, rule-based re-framings of existing columns -- ported from `notebooks/exploratory_analysis.py`'s Lenses 1/2/3/4/5/6/8 into a reusable `compute_axes(row, activist_columns)` function:

- `consent` -- alias of `board_recommendation_code`.
- `price_discovery_type` -- one of "Single negotiated, no bump", "Bumped, board aligned", "Bumped, board split", "Bidding war (bumped + competing bid)", "MBO with interloper risk", "MBO, single negotiated price", derived from `price_was_bumped_bool` x `board_recommendation_code` x `competing_bid_flag` x `structure_has_MBO`.
- `regulatory_friction` -- "Multi-jurisdiction" / "Domestic/single-jurisdiction" from `num_regulators`.
- `precedent_value_text` -- `{'text': notes_raw, 'flagged_precedent_setting': bool}`.
- `instigator_type` -- Activist-instigated / Sponsor-instigated / Strategic-instigated.
- `lockup_signal_count` -- 0-3 from `toehold_present_flag` + `special_committee_flag` + `recurring_acquirer_flag`.
- `activist_signature` -- sorted, comma-joined named funds, or `None`.

These axis values are the intended basis for grouping cases into overlapping archetypes in the Part 3 scenario-playbook UI (not yet built -- see `Roadmap.md`); a case naturally carries several axis values at once, which is exactly the overlapping-membership behavior `Claude.md` requires.

### Community detection (secondary/diagnostic cross-check, not the primary cluster definition)

`precedent_engine.py` also builds a full (untrimmed) pairwise graph -- an edge for every pair scoring >= `COMMUNITY_MIN_SCORE`, reusing `pair_score()` so "similar" means the same thing everywhere -- and runs `networkx.algorithms.community.k_clique_communities(G, k=K_CLIQUE)` on it. This is explicitly a cross-check against the axis tags above, not a replacement.

**Tuned 2026-07-07** (was degenerate at `k=3`/`MIN_SCORE=1.5`, reusing the viewer's threshold -- see `docs/To-do.md` 2026-07-07 for the full investigation). Root cause was two-fold: `MIN_SCORE=1.5` let 79.7% of all 1,891 pairs "connect" (31.6% from just 6 near-universal features alone), *and* k-clique percolation on this corpus's feature-sharing structure converges to one dominant community regardless of threshold -- verified by a grid search up to threshold=9.0, which always left one big "generic-deal" community plus a few small (3-6 node) satellite communities of genuinely rare-feature-driven cases. That split is real (most of the 62 cases share fairly ordinary combinations; only a handful share truly distinctive ones), not fixable by threshold alone.

`COMMUNITY_MIN_SCORE=7.0` and `K_CLIQUE=3` were chosen as a more balanced, useful split over maximizing node coverage -- currently produces 5 communities (sizes `[16, 3, 3, 3, 3]`, 26/62 nodes covered; the remaining 36 nodes have no `community_ids` entry, meaning no unusually tight cluster of close precedents -- itself informative, not a gap to fill). `COMMUNITY_MIN_SCORE` is intentionally separate from the viewer's `MIN_SCORE=1.5` (unchanged, still governs the top-4 trim only). Revisit both constants once Part 3 builds a UI that actually consumes `community_ids` -- what reads well in a chart may call for different parameters than this text-only review used.

### `short_name` (added 2026-07-06)

Each node gets a compact display label for the viewer's on-circle text (the full `target_full_name` cluttered the force-graph layout). Mechanical string cleanup only, no new facts: strip parenthetical content, then iteratively strip a trailing stoplist of generic corporate suffixes (Corporation, Corp., Co., Ltd., Inc., Holdings, Group, Company, etc.), trim trailing punctuation, and fall back to the name's first 3 words if the result is empty. See this session's `Changelog.md` entry for the full before/after table across all 62 rows, manually reviewed before shipping (per this project's "verify before trusting" convention -- a prior text-matching heuristic elsewhere in this project produced bad false positives and was caught this way). A few long names with no parenthetical/suffix to strip (e.g. JP-047 "Macquarie's US & European public asset management business", JP-058 "Renesas Electronics -- timing products business") remain long by design -- there was nothing mechanical to remove.

## Part 3 -- interactive viewer (`viewer/Japan_Precedent_Constellation.html`)

**One line changed this session**: the always-visible node label under each circle now renders `d.short_name` instead of `d.id` (deal_id is unchanged everywhere else -- detail panel, search). Otherwise unmodified. Self-contained D3.js force-directed graph with two modes:

- **Explore mode**: browse the precomputed precedent graph; click a node to see its brief and top precedent links with reasons.
- **Find Precedent mode**: score a hypothetical new deal's facts against all 62 cases using the same weighting scheme.

No report-generation feature exists yet (see `Roadmap.md`).
