# Japan Special Situations — Project Handoff

**Purpose of this doc:** context for a fresh Claude Code or Cowork session picking up this project. Read this before touching the files — it explains *why* things are built the way they are, not just what exists.

## What this project is

A case-based precedent library for Japanese M&A/takeover/activism special situations (2023–2026H1), built for **qualitative pattern study**, explicitly *not* for quantitative trading signals. The end goal: given a new deal's facts, quickly surface comparable historical precedents and see what typically happened — a "case-law playbook," not a predictive model.

## How the tool is meant to be used (product vision)

Think of it the way a lawyer thinks about case law, not the way a quant thinks about a model:

1. **Input** — a handful of facts about a new/hypothetical deal (deal structure, industry, regulators likely in play, activist presence, board posture, etc.).
2. **Retrieval** — the similarity engine (Part 2) surfaces the most comparable historical cases from the 62-deal corpus, using the weighted feature-match scoring already in `precedent_engine.py`.
3. **Clustering** — those precedents aren't a single flat list; they group into **clusters** representing recognizable deal archetypes/situations (e.g. "board-consent take-private," "hostile bid with late interloper," "cross-border outbound with multi-jurisdiction FDI review"). **A given case can and should belong to more than one cluster** — clustering here is soft/overlapping, not a hard partition, because real deals genuinely have multiple simultaneous characteristics (e.g. Fuji Soft is both a hostile/consentless bid *and* a cross-border-sponsor deal *and* an interloper/lock-up case). Part 2 needs to design for multi-membership from the start, not bolt it on later.
4. **Output — the scenario playbook.** For each relevant cluster, the tool displays a "probability tree" / scenario playbook: a descriptive map of what actually happened across that cluster's precedents (which resolution mechanisms occurred, how outcomes split, what the regulatory/timeline friction looked like, what debate points recurred). This is **descriptive pattern frequency across comparable precedents, not a predictive probability computed for the new deal** — it does not say "this deal has an X% chance of succeeding." It says "among the N comparable precedents in this cluster, here is the distribution of what happened." This framing must be preserved carefully in any Part 2/3 work so the tool doesn't drift into the predictive-modeling territory ruled out below.

This case-law mental model — precedent retrieval → cluster → scenario playbook, never single-number prediction — is the framing for all of Part 2 and Part 3 work.

## Repo layout

The project is organized as `data/`, `src/`, `docs/`, `output/`, `viewer/` (see `docs/Architecture.md` for the full data-flow diagram — this section is just a pointer, don't duplicate detail here).

| Path | What it is |
|---|---|
| `data/Japan_Master.csv` | Original source: 62 hand-curated landmark Japan M&A/activism situations, 2023–2026H1, free-text/narrative fields. |
| `data/Japan.csv` | ML/analysis-ready recoding of the master file: every messy field split into `_raw` (original text, untouched) + parsed value + `_is_estimate` flag + boolean/categorical breakdowns. 139 columns, 62 rows (see `docs/Changelog.md` for the running history of schema additions). |
| `data/Japan_Codebook.csv` | Lookup table for every label-encoded `*_code` column in `Japan.csv`. |
| `docs/Japan_README.md` | Source methodology, conventions, regulatory map, known limitations. |
| `docs/Japan_User_Guide.md` | Full field-by-field dictionary for `Japan.csv`. |
| `docs/Regulatory_Timeline_Appendix.md` | Substantive background on the three regulatory regimes (METI 2023 guidelines, TSE reform, FIEA amendment) behind the `timeline_post_*` columns — what changed and why it matters, with sourced links. |
| `src/explore.py` | Part 1: adaptive data-quality report + visualizations, generated from `data/Japan.csv` into `output/`. |
| `src/cluster/precedent_engine.py` | Part 2: computes a transparent, rule-based similarity score between every pair of the 62 cases (weighted match on category/industry/structure/regulators/named activists), outputs `output/precedent_graph_data.json`. Also attaches per-case axis tags (`src/cluster/axes.py`) as the primary overlapping-cluster signal and a secondary k-clique community-detection cross-check — see `docs/Architecture.md`. No UI browses these yet; that's Part 3, see `docs/Roadmap.md`. |
| `src/cluster/axes.py` | Part 2: descriptive per-case "axis" dimensions (consent, price-discovery type, regulatory friction, precedent-value text, instigator identity, lock-up signal count, activist signature) feeding the overlapping-cluster design above, plus a Jaccard co-occurrence helper for double-counting checks. |
| `output/precedent_graph_data.json` | Computed nodes + edges + weights consumed by the HTML viewer. Regenerate after any edit to `data/Japan.csv` or to the weights in `precedent_engine.py`. Gitignored (regenerable). |
| `viewer/Japan_Precedent_Constellation.html` | Self-contained interactive viewer (D3.js force graph). "Explore" mode browses precedent links; "Find Precedent" mode scores a hypothetical new deal against all 62 cases. |

**Running trackers (read/update these as work progresses, not this file):** `docs/Architecture.md` (current node/edge/cluster semantics), `docs/Changelog.md` (dated history), `docs/To-do.md` (open manual-verification items), `docs/Roadmap.md` (Part 1/2/3 status — built vs. planned).

## Key decisions already made (don't re-litigate these without reason)

1. **Scope is 62 rows only** — `Japan_Watchlist.csv` (rumor-stage situations) was deliberately excluded from `Japan.csv`.
2. **No new facts were ever introduced.** Every derived column is either a direct copy or a mechanical parse/keyword flag off an existing source cell. If you add features, keep this discipline — it's what makes the `_raw` columns trustworthy.
3. **This is explicitly not a quant/ML training set.** n=62 is a hand-picked, non-random, precedent-setting sample (survivorship/selection bias by design — these are "the famous ones"). Do not build predictive models on it or represent outputs as statistically validated. It's a comparison/lookup tool.
4. **Similarity weights in `precedent_engine.py` are a legal/practitioner judgment call, not fitted.** Rare, strong signals (CFIUS review, named activist fund, scheme of arrangement) are weighted higher than near-universal, weak ones (JFTC review, which touches almost every deal). If you disagree with a weight, change the constant — that's expected and the whole point of keeping this rule-based rather than a black box.
5. **Graph is trimmed to top-4 nearest neighbors per node** (min score threshold 1.5) specifically so the rendered chart stays legible — a complete graph on 62 nodes is a hairball, not an insight. Don't remove this trimming without a reason.
6. **Clustering must support multi-membership.** Per the product vision above, a case can belong to more than one cluster (a deal can simultaneously be "hostile," "cross-border," and "interloper" archetypes). The current `precedent_engine.py` produces a single flat nearest-neighbor graph, not labeled overlapping clusters — that redesign is Part 2 scope (see `docs/Roadmap.md`), not yet built. Don't assume today's graph already does this.

## Known data-quality issues to keep in mind

- **Final offer price**: missing in 44% of rows; of what's present, 18% is flagged as an estimate ("TBV"/"≈"/"~").
- **Unaffected (pre-deal) price**: missing in 76% of rows; 65% of what's present is an estimate.
- **Headline premium %**: missing in 55% of rows; 66% of what's present is an estimate.
- **33 of 62 rows** are "Medium – needs verification" per the source's own confidence grading; 2 are "Low."
- **`category_raw` and `industry_raw` are ~90% unique** (56/62, 58/62 distinct values) — never model on these directly, use `category_group`/`industry_group`.

**Do not treat any TBV/estimate-flagged number as fact in written output.** If a user-facing case study cites a specific price or premium, check the `_is_estimate` flag first and caveat accordingly.

## Recommended next steps

Tracked live in `docs/To-do.md` (manual verification items/decisions) and `docs/Roadmap.md` (Part 1/2/3 status) — check those rather than this file, which is not kept in sync with day-to-day progress. As of the last update to this file, open items include: primary-source verification of "Medium"/"Low" confidence rows, a structured `precedent_established` field, and a regulatory-timeline overlay.

**Part 2's overlapping-clustering layer now exists** (axis tags as the primary multi-membership mechanism, k-clique community detection as a secondary diagnostic cross-check) — see `docs/Architecture.md` for how it works. Part 3's scenario-playbook UI to actually browse those clusters is still not built.

## What NOT to do

- Don't add trading/quant framing (premium regressions, predictive scoring) — that was explicitly ruled out; this is a case-study tool.
- Don't silently resolve TBV values to specific numbers — if you verify one, update the `_raw` column too and change the `_is_estimate` flag, so the audit trail stays intact.
- Don't regenerate `Japan.csv` from `Japan_Master.csv` without preserving the parsing conventions in the (already-written, not included here) build script — ask the user if they want that script re-shared.
