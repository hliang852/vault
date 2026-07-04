# Architecture

Describes the **current, built state** of the repo. Planned-but-unbuilt work lives in `Roadmap.md`, not here.

## Repo layout

```
data/     source CSVs (Japan_Master.csv, Japan.csv, Japan_Codebook.csv, Japan_Watchlist.csv, masterfile.xlsx)
src/
  explore.py            Part 1 -- data exploration & visualization
  cluster/
    precedent_engine.py Part 2 -- similarity scoring + graph construction
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
