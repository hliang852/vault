# Japan Special Situations — Project Handoff

**Purpose of this doc:** context for a fresh Claude Code or Cowork session picking up this project. Read this before touching the files — it explains *why* things are built the way they are, not just what exists.

## What this project is

A case-based precedent library for Japanese M&A/takeover/activism special situations (2023–2026H1), built for **qualitative pattern study**, explicitly *not* for quantitative trading signals. The end goal: given a new deal's facts, quickly surface comparable historical precedents and see what typically happened — a "case-law playbook," not a predictive model.

## Files in this project (all in the working directory)

| File | What it is |
|---|---|
| `Japan_Master.csv` | Original source: 62 hand-curated landmark Japan M&A/activism situations, 2023–2026H1, free-text/narrative fields. |
| `Japan_README.md` | Source methodology, conventions, regulatory map, known limitations. |
| `Japan.csv` | ML/analysis-ready recoding of the master file: every messy field split into `_raw` (original text, untouched) + parsed value + `_is_estimate` flag + boolean/categorical breakdowns. 128 columns, 62 rows. |
| `Japan_Codebook.csv` | Lookup table for every label-encoded `*_code` column in `Japan.csv`. |
| `Japan_User_Guide.md` | Full field-by-field dictionary for `Japan.csv`. |
| `precedent_engine.py` | Python scorer: computes a transparent, rule-based similarity score between every pair of the 62 cases (weighted match on category/industry/structure/regulators/named activists), outputs `precedent_graph_data.json`. |
| `precedent_graph_data.json` | Computed nodes + edges + weights consumed by the HTML viewer. Regenerate after any edit to `Japan.csv` or to the weights in `precedent_engine.py`. |
| `Japan_Precedent_Constellation.html` | Self-contained interactive viewer (D3.js force graph). "Explore" mode browses precedent links; "Find Precedent" mode scores a hypothetical new deal against all 62 cases. |

## Key decisions already made (don't re-litigate these without reason)

1. **Scope is 62 rows only** — `Japan_Watchlist.csv` (rumor-stage situations) was deliberately excluded from `Japan.csv`.
2. **No new facts were ever introduced.** Every derived column is either a direct copy or a mechanical parse/keyword flag off an existing source cell. If you add features, keep this discipline — it's what makes the `_raw` columns trustworthy.
3. **This is explicitly not a quant/ML training set.** n=62 is a hand-picked, non-random, precedent-setting sample (survivorship/selection bias by design — these are "the famous ones"). Do not build predictive models on it or represent outputs as statistically validated. It's a comparison/lookup tool.
4. **Similarity weights in `precedent_engine.py` are a legal/practitioner judgment call, not fitted.** Rare, strong signals (CFIUS review, named activist fund, scheme of arrangement) are weighted higher than near-universal, weak ones (JFTC review, which touches almost every deal). If you disagree with a weight, change the constant — that's expected and the whole point of keeping this rule-based rather than a black box.
5. **Graph is trimmed to top-4 nearest neighbors per node** (min score threshold 1.5) specifically so the rendered chart stays legible — a complete graph on 62 nodes is a hairball, not an insight. Don't remove this trimming without a reason.

## Known data-quality issues to keep in mind

- **Final offer price**: missing in 44% of rows; of what's present, 18% is flagged as an estimate ("TBV"/"≈"/"~").
- **Unaffected (pre-deal) price**: missing in 76% of rows; 65% of what's present is an estimate.
- **Headline premium %**: missing in 55% of rows; 66% of what's present is an estimate.
- **33 of 62 rows** are "Medium – needs verification" per the source's own confidence grading; 2 are "Low."
- **`category_raw` and `industry_raw` are ~90% unique** (56/62, 58/62 distinct values) — never model on these directly, use `category_group`/`industry_group`.

**Do not treat any TBV/estimate-flagged number as fact in written output.** If a user-facing case study cites a specific price or premium, check the `_is_estimate` flag first and caveat accordingly.

## Recommended next steps (not yet done)

1. **Primary-source verification pass** on the 33 "Medium" + 2 "Low" confidence rows — cross-check against EDINET tender offer registration statements (公開買付届出書) and TDnet filings before relying on any of them in written analysis.
2. **`situation_id` linking** — currently, multi-bid contests (e.g. Seven & i/Couche-Tard vs. York/Bain; Nidec/Makino vs. MBK/Makino) are separate unlinked rows. Add a field grouping rows that belong to the same underlying situation.
3. **`precedent_established` field** — a standardized one-sentence extraction of "what rule/norm this deal is the reference case for," pulled from the existing `notes_raw` / `key_debate_points_raw` text (which already contains this informally, just not structured).
4. **Regulatory timeline overlay** — plot deal announcement dates against actual rule changes (METI Aug 2023 guidelines, TSE reform, FIEA amendment effective 2026/05/01) since deal flow clusters heavily in 2024–2025, right after the guidelines took effect.
5. If the corpus needs to grow beyond 62 for broader pattern coverage, the natural source is a licensed feed (Bloomberg `MA<GO>`, Refinitiv/LSEG, MARR/RECOF) rather than more manual curation.

## What NOT to do

- Don't add trading/quant framing (premium regressions, predictive scoring) — that was explicitly ruled out; this is a case-study tool.
- Don't silently resolve TBV values to specific numbers — if you verify one, update the `_raw` column too and change the `_is_estimate` flag, so the audit trail stays intact.
- Don't regenerate `Japan.csv` from `Japan_Master.csv` without preserving the parsing conventions in the (already-written, not included here) build script — ask the user if they want that script re-shared.
