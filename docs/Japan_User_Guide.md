# Japan.csv — User Guide

**What this is:** a machine-learning-ready recoding of `Japan_Master.csv` (the 62-deal Japan M&A/takeover/activism masterfile, 2023–2026H1). One row = one deal/situation, same as the source file. No new facts, prices, dates, or deals have been added — every value in `Japan.csv` is either copied unchanged from the source or mechanically derived from a source cell (parsed number, keyword flag, categorical grouping, or label code).

Companion file: **`Japan_Codebook.csv`** — the lookup table for every `*_code` / `*_code_num` column (code → text label).

---

## 1. How to read this file

For nearly every source field, `Japan.csv` provides up to four parallel columns:

| Suffix | Meaning |
|---|---|
| `_raw` | The original text from `Japan_Master.csv`, unmodified. Always kept so nothing is lost. |
| `_value` / no suffix (numeric) | The number mechanically extracted from `_raw` (e.g. "≈¥4,350 (TBV)" → `4350`). |
| `_currency` / `_code` | A short categorical tag extracted or assigned from `_raw` (currency, category, exchange, etc.). |
| `_is_estimate` | `True` if the source text contained a hedge marker — "TBV", "≈", "~", "approx.", "expected" — meaning the underlying masterfile author flagged this number as unverified or approximate. **Always check this flag before using a numeric field in analysis.** |

Boolean columns (`True`/`False`) are keyword-derived flags — e.g. `structure_has_TOB` is `True` if the word "TOB" appears anywhere in `Deal Structure`. These are pattern flags, not independently verified facts; if the source text didn't mention something, the flag is `False`, which is not the same as "confirmed absent."

Blank cells mean the source cell was blank/not applicable, or a number/keyword could not be confidently parsed from free text.

---

## 2. Column-by-column dictionary

### Identifiers & classification
| Column | Description |
|---|---|
| `deal_id` | Source deal ID (JP-001…JP-062). Primary key. |
| `category_raw` | Original, highly specific situation category (56 near-unique values over 62 rows — expect one-off text, not a clean taxonomy). |
| `category_group` | Coarser bucket derived from `category_raw` by keyword: `Activist campaign`, `Take-private / MBO`, `Cross-border outbound`, `Parent-subsidiary / carve-out`, `Contested / hostile bid`, `Strategic TOB`, `Other`. Use this for grouping/modeling; use `category_raw` for lookup/detail. |
| `category_code`, `category_group_code` | Integer label-encoding of the two columns above. See `Japan_Codebook.csv`. 0 = blank. |

### Dates & duration
| Column | Description |
|---|---|
| `date_announced` | ISO format (`YYYY-MM-DD`). |
| `date_announced_precision` | `day` (always, for this column). |
| `date_announced_year` | Convenience year extract. |
| `date_completed_or_failed` | ISO date, month (`YYYY-MM`), or year (`YYYY`) depending on how precise the source cell was. |
| `date_completed_precision` | `day` / `month` / `year` / blank (unresolved, e.g. "TBV"). |
| `time_to_close_months` | Copied from source (already computed there per the source's own methodology: (completion − announcement)/30.44). |
| `conclusion_status_raw` | Original free-text status. |
| `outcome_code` | Simplified to `Concluded`, `Failed`, or `Other/Unclear`. |
| `outcome_code_num` | Integer code for `outcome_code`. |

### Target & acquirer
| Column | Description |
|---|---|
| `target_full_name`, `acquirer_full_name` | Copied as-is. |
| `target_ticker_exchange_raw` | Original "ticker / exchange" text. |
| `target_ticker_code` | Numeric Japanese ticker only (e.g. `6502`), extracted where the target is JP-listed; blank for foreign/unlisted targets (see `_raw` for those). |
| `target_exchange`, `target_exchange_code` | Cleaned exchange label (e.g. "TSE Prime", "NYSE", "Unlisted") + its label code. |
| `industry_raw` | Original, highly specific industry text (58 near-unique values). |
| `industry_group`, `industry_group_code` | Coarser sector bucket (Financials, Semiconductors/electronics, Industrials/machinery, Retail/consumer, Energy, Healthcare/pharma, HR/staffing/services, Technology/software, Automotive/mobility, Printing/materials, Other). |
| `acquirer_exchange_raw` | Original text. |
| `acquirer_is_unlisted` | `True` if that text contains "Unlisted". |

### Deal size
| Column | Description |
|---|---|
| `deal_size_usd_mn` | Numeric value from "Deal Size (US$ mn)". |
| `deal_size_usd_is_estimate` | Hedge-marker flag (see §1). |
| `deal_size_usd_is_stake_value` | `True` when `category_raw` contains "Activist" — per the source README, activist-campaign rows report **stake value**, not full deal value, in the size columns. Check this before comparing deal sizes across rows. |
| `deal_size_local_value_bn`, `..._currency`, `..._is_estimate` | Local-currency size, normalized to **billions** (values reported in "tn" were multiplied ×1000 and flagged in `deal_size_local_scale_note`). Currency is JPY unless the source cell specified otherwise (e.g. AUD for the Altium/Australia deal). |
| `deal_size_local_scale_note` | `converted_tn_to_bn`, `bn`, or blank — tells you whether/how a unit conversion was applied. |

### Deal structure & pricing
| Column | Description |
|---|---|
| `deal_structure_raw` | Full original text — kept whole because it's often a compact multi-fact narrative (structure + price + conditions). |
| `structure_has_TOB` / `_squeeze_out` / `_MBO` / `_merger` / `_scheme` / `_share_sale` / `_proxy_contest` | Boolean flags for whether each mechanism keyword appears in `deal_structure_raw`. A deal can have several `True` flags at once (e.g. an MBO executed via TOB + squeeze-out). |
| `final_offer_price_value/_currency/_is_estimate/_raw` | The final/last price per share (or per-unit) offered. |
| `initial_offer_price_value/_currency` | The first price mentioned in "Initial Offer / Price Bumps". |
| `price_bump_count` | Number of price increases, parsed from explicit "(N bumps)" text or by counting "→" arrows in the bump narrative. Blank = could not be determined. |
| `price_was_bumped` | `True`/`False`, or `Unclear/TBV` when the source only said "TBV" with no bump detail. |
| `price_was_bumped_bool` | Clean boolean version of `price_was_bumped` (added 2026-07-06): `True` only where that column is literally `True`; `Unclear/TBV` and blank both become `False`. Added because the mixed-type source column is unsafe to feed directly into boolean logic (a non-empty string like `Unclear/TBV` is Python-truthy). Use this one for any flag-style analysis; use `price_was_bumped` when the Unclear/TBV distinction matters. |
| `initial_offer_price_bumps_raw` | Full original bump narrative — richer than the parsed fields above; read this for deal-specific detail (who bumped, in response to what). |
| `unaffected_price_value/_currency/_is_estimate/_raw` | Pre-announcement/pre-rumor share price, where the source estimated one. |
| `premium_pct_value/_is_estimate/_raw` | Headline premium to unaffected price. Note: some source cells describe a premium to a different reference (e.g. "90-day VWAP") in the same string — read `_raw` if the reference point matters. |

### Governance & deal process
| Column | Description |
|---|---|
| `board_recommendation_raw` | Original text. |
| `board_recommendation_code`, `_code_num` | Simplified to `For`, `Opposed`, `Mixed`, `Engaged`, `No formal recommendation`, `Unclear/TBV`, `Other`. |
| `special_committee_raw`, `special_committee_flag` | Flag simplified to `Yes` / `No` / `Unclear/TBV` / `Other`. |
| `competing_bid_raw`, `competing_bid_flag` | `Yes` / `No` / `Unclear/TBV`, based on whether the text describes a rival bid/auction or explicitly says none emerged. |
| `recurring_acquirer_raw`, `recurring_acquirer_flag` | Whether the acquirer had a prior/serial relationship with the target (`Yes`/`No`/`Unclear/TBV`). |
| `financial_advisor_target_raw`, `financial_advisor_acquirer_raw` | M&A financial advisor(s) named for the target side and the acquirer side, respectively (added 2026-07-06; pilot batch of 7/62 rows researched from public tender-offer filings/press releases, remaining 55 rows and `JP-003` are `TBV` pending research). Free text, semicolon-separated when multiple firms are named (e.g. distinct advisors to the management team vs. the independent special committee) — not yet split into atomic columns. Always check for `TBV` before citing; do not assume a blank-looking pilot list is exhaustive. |
| `target_ipo_advisor_raw` | Lead underwriter(s) of the target company's original IPO/listing (added 2026-07-06). Currently `TBV` for all 62 rows — pilot research found this materially harder to verify publicly than M&A advisors (conflicting listing-year and underwriter claims surfaced even for recent IPOs like Benefit One and Outsourcing Inc.), so no row has been populated yet. See `docs/To-do.md` for the decision to hold this column pending better sourcing. |
| `toehold_raw` | Original text (pre-existing stake, irrevocables, tender agreements). |
| `toehold_present_flag` | `True` if some toehold/irrevocable arrangement is described (i.e. not blank and not "No toehold"). |
| `toehold_pct_value`, `toehold_is_estimate` | First percentage figure found in the toehold text, if any (a row can reference more than one party's stake — see `_raw` for full detail). |

### Regulatory
| Column | Description |
|---|---|
| `regulator_1_raw/2_raw/3_raw` | Original three regulator-mention columns. |
| `num_regulators` | Count of the three columns that are non-blank and not "—". |
| `multi_jurisdiction` | Boolean convenience flag (added 2026-07-06): `num_regulators >= 2`. Mirrors the "regulatory friction" lens in `notebooks/exploratory_analysis.py`. |
| `has_JFTC`, `has_FSA`, `has_METI`, `has_CFIUS`, `has_FEFTA`, `has_China_SAMR`, `has_EU_regulator`, `has_DOJ_FTC_HSR`, `has_FIRB`, `has_SEC`, `has_Bermuda_BMA`, `has_Broadcast_Act` | Boolean — regulator name/acronym found anywhere across the three regulator cells. |
| `has_dual_antitrust_review` | Boolean convenience flag (added 2026-07-07): `has_JFTC AND has_DOJ_FTC_HSR`. Added after an empirical review found these two correlate meaningfully above base rate (not just because both are common) — used in `precedent_engine.py`'s similarity score in place of scoring the two separately, to avoid double-counting one underlying "faces overlapping antitrust review" fact. `has_JFTC`/`has_DOJ_FTC_HSR` themselves are unchanged and still usable independently. *(Re-affirmed 2026-07-12 on the integrated 110-case corpus, where the original subset/correlation rationale no longer holds — kept as a deliberately rare "dual-review" signal, 4/110 true; see `To-do.md` 2026-07-12.)* |
| `has_other_foreign_antitrust_or_FDI` | `True` if the regulator text mentions generic "foreign antitrust", "merger control", or "FDI screening" not captured by a named flag above. |
| `rules_regulations_triggering_review_raw` | Original text (kept whole — usually a dense, deal-specific legal narrative). |
| `mentions_FIEA`, `mentions_METI_guidelines`, `mentions_Companies_Act`, `mentions_FEFTA`, `mentions_CFIUS`, `mentions_TSE_reform` | Boolean keyword flags on that same text. |
| `timeline_post_meti_2023_guideline`, `timeline_post_tse_reform_2023`, `timeline_post_fiea_2026_amendment` | Regulatory-timeline overlay (added 2026-07-06). Boolean, derived mechanically from `date_announced` vs. each rule's real-world effective date — **not** a text-mention flag like the `mentions_*` columns above, and not mutually exclusive with them (a deal can mention METI guidelines in its narrative while still predating the actual guideline date, or vice versa). Effective dates used: METI Corporate Takeover Guidelines 2023-08-31, TSE cost-of-capital/PBR reform request 2023-03-31, FIEA mandatory-TOB amendment 2026-05-01 (the last is `True` for zero rows in the current 62-case corpus, since the corpus ends before any post-amendment announcement). |
| `timeline_post_2023_reforms` | Boolean convenience flag (added 2026-07-07): `timeline_post_meti_2023_guideline AND timeline_post_tse_reform_2023`. Raw co-occurrence between the two source flags was high (0.93 Jaccard), but an empirical lift check found this was almost entirely explained by both simply being common (85%/92% true) rather than genuine redundancy. Consolidated anyway into this single column for `precedent_engine.py`'s similarity scoring, per an explicit maintainer decision to be cautious rather than because the statistics required it — the two source columns are unchanged and still independently usable. `timeline_post_fiea_2026_amendment` was deliberately left out of this consolidation (different rule, different effective date, currently inert regardless). |

### Activism
| Column | Description |
|---|---|
| `key_debate_points_raw` | Original free text — not atomized; every row's debate points are essentially unique narrative. |
| `activism_involvement_raw` | Original text. |
| `has_activist_involvement` | `True` unless the text is a "none" variant (e.g. "None named", "None material") or "TBV". |
| `activist_Effissimo`, `activist_Farallon`, `activist_Elliott`, `activist_3D_Investment`, `activist_King_Street`, `activist_ValueAct`, `activist_Oasis`, `activist_Murakami`, `activist_YFO`, `activist_Dalton`, `activist_Ancora`, `activist_Artisan_Partners`, `activist_MY_Alpha`, `activist_Palliser` | One boolean column per named fund that appears anywhere in the masterfile's activism column — `True` if that specific fund is named in this row. Unnamed "event funds" / generic references are captured only by `has_activist_involvement`, not by a named-fund column. |

### Resolution & verification
| Column | Description |
|---|---|
| `final_resolution_mechanism_raw` | Original text. |
| `resolution_delisted_flag`, `resolution_squeeze_out_flag`, `resolution_withdrawn_flag` | Boolean keyword flags on that text. |
| `squeeze_out_mechanism_raw`, `squeeze_out_mechanism_code(_num)` | Simplified to `Share consolidation`, `Merger`, `Scheme of arrangement`, `Share exchange`, `Unclear/TBV`, or blank. |
| `delisting_date_raw`, `delisting_date`, `delisting_date_precision`, `delisting_date_is_estimate` | Same day/month/year parsing logic as the announcement/completion dates. |
| `verification_status_raw`, `verification_confidence_code(_num)` | Simplified to `Verified via current search (Jul 2026)`, `High confidence`, `Medium - needs verification`, `Low - needs verification`, `Unclear`. **Treat `Medium`/`Low`/`Unclear` rows as needing primary-source verification before any external use — this mirrors the masterfile's own caveat.** |
| `notes_raw` | Original analyst notes, unmodified. |
| `notes_flags_precedent_setting` | Boolean keyword flag on `notes_raw` (added 2026-07-06): `True` if the notes contain (case-insensitive) any of "first", "template", "precedent", "proof-of-concept", "landmark", "signature". Mechanical text flag in the same spirit as `structure_has_*` / `mentions_*` — not a verified judgment that the deal set a precedent. |

---

## 3. Using the codebook

Any column ending in `_code` or `_code_num` is an integer label-encoding. Look up the text meaning in `Japan_Codebook.csv`, filtering `field` to the column name, e.g.:

```
field == "industry_group_code"  →  code 3 = "Industrials / machinery"
```

Code `0` always means "missing/blank" in the source.

---

## 4. Known limitations (carried over from the source masterfile)

- **Coverage:** 62 hand-selected landmark situations, not a complete database of all >US$100mn Japan M&A in the period (see `Japan_README.md` §2a for why — a complete universe needs a licensed database).
- **TBV cells:** many prices, premiums, dates, and stakes are best-recollection estimates flagged "TBV" in the source; this file preserves those flags via `_is_estimate` / `Unclear` codes rather than resolving them. Do not treat an `_is_estimate = True` value as confirmed.
- **Keyword flags are text-derived, not fact-checked.** A `False` flag means the keyword wasn't found in the relevant cell — it does not certify the underlying condition is absent (e.g. `has_CFIUS = False` means CFIUS wasn't named in the regulator columns, not that CFIUS definitely had no role).
- **High-cardinality raw categoricals.** `category_raw` and `industry_raw` are close to one-of-a-kind per deal; use the `_group` versions for any grouping, cross-tab, or model feature.
- No rows from `Japan_Watchlist.csv` (rumor-stage situations) are included, per scope confirmed for this file.

For full methodology, conventions, and the regulatory map, see `Japan_README.md`.
