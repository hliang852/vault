# Japan M&A Masterfile — Sources & Citation Methodology

**Purpose:** records (a) how the original 62-row masterfile was actually researched, (b) the source hierarchy that governs all research from now on (backfill, scope expansion, manual additions, and the Track 2 daily scanner), and (c) the citation and language conventions.

---

## 1. Honest record: how the original 62 rows were built

The Phase 1 masterfile (compiled 2026/07/03) was **not** built from a systematic scrape. It was assembled primarily from the model's trained knowledge of landmark situations, spot-checked with a small number of targeted web searches for the most recent or uncertain items. Where a value was not confidently known, the cell was written **TBV** rather than filled with a guess, and the row was graded in the Verification Status column. Secondary references that informed spot checks (visible in the Verification Status cells) include Reuters/Nikkei-derived coverage, Lexology and Chambers practice notes, JPM/Dealogic and RECOF summaries, and DealStreetAsia.

**Consequence:** the original rows carry no attached source URLs. A citation backfill (batch verification passes, deal by deal) is required to bring the historical rows up to the standard defined below. Backfill status is tracked in the Source URL columns themselves (`TBV — citation backfill pending`) until each row is done.

## 2. Source hierarchy (governs all tracks)

Sources are tiered. **Source URL 1 must be Tier 1 wherever a Tier 1 source exists for the situation.** Tiers 2–3 support context fields (debate points, interlopers, rumor status). Tier 4 may be used for discovery only, never as citation of record.

### Tier 1 — Primary / regulatory (citation of record)
| Source | What it provides | Access |
|---|---|---|
| **EDINET** (`disclosure2.edinet-fsa.go.jp`) | Tender offer registration statements (公開買付届出書), target board opinion statements (意見表明報告書), amendment statements (訂正届出書), large shareholding reports (大量保有報告書, activist stakes), securities reports | Official FSA **API** (free, JSON document index + document retrieval); the backbone of the Track 2 scanner |
| **TDnet** (`release.tdnet.info`) | Timely-disclosure press releases: TOB announcements/launches, board opinions, price bumps, results, delisting notices | Web; no official public API — scanner access method to be settled at build time (direct listing-page fetch vs. licensed feed), with ToS reviewed |
| **Company IR pages** (target and bidder) | Bilingual deal press releases, TOB microsites (e.g., taiyo-hd.co.jp TOB page) | Web |
| **Courts / government** | Appraisal and injunction decisions (courts.go.jp), JFTC clearances, METI/MoF FEFTA statements, CFIUS/White House orders, SEC filings for US-listed parties | Web |

### Tier 2 — Quality press (context; rumor-stage detection), in this order of preference
1. **Nikkei / Nikkei Asia**
2. **Reuters**
3. **Bloomberg**

These are paywalled; the scanner treats them as headline/lede-level detection and citation-linking, not full-text scraping. Syndicated Reuters copies on open sites are acceptable citations when the original is paywalled, with the original outlet named in the cell text.

### Tier 3 — Professional secondary
Law-firm memos and practice notes (Lexology, Chambers, firm publications), bank/advisor deal summaries, MARR/RECOF statistics. Good for regulatory-mechanics fields; always subordinate to Tier 1 on dates/prices.

### Tier 4 — Aggregators / feeds (discovery only)
TDnet mirror feeds, market-data aggregators, Substacks. Never cited as source of record.

## 3. Citation conventions

- Three dedicated columns on every row: **Source URL 1 (primary)**, **Source URL 2**, **Source URL 3** — one citation per column, per the file owner's instruction.
- Source URL 1: Tier 1 where it exists; otherwise the highest available tier, with the gap noted in Notes.
- A cell-level fact that comes from a source other than URL 1–3 must not be entered; either add/replace a citation column's URL or leave the cell TBV.
- Rows whose citations are not yet attached carry `TBV — citation backfill pending` in Source URL 1. **No row may be graded `Verified` without at least Source URL 1 populated.**
- `Japan_new.csv` (Track 2) rows must **never** be created without at least one citation; rumor-stage rows cite the media report and are labeled `Media report / rumored`.

## 4. Language convention (Japanese primary sources)

Most Tier 1 documents are Japanese. The rule, per the file owner's instruction:
- **Preserve the Japanese as-is** in a raw column (`Original Source Title / Excerpt (JA raw)` in `Japan_new.csv`; filing titles quoted in Notes for the master) so it can be re-verified against the filing later.
- Provide an **English translation alongside** (`Translation (EN)`), marked as a working translation; the Japanese text prevails.
- Where a company publishes its own English translation (common for TOB documents), cite that document but retain the Japanese title.

## 5. Verification workflow (backfill & new research)

Per deal: (1) locate the Tier 1 filing(s) on EDINET/TDnet/company IR; (2) confirm or correct announcement date, offer price(s)/bumps, deal size, board opinion, special committee, toehold/irrevocables, completion/delisting; (3) attach Source URL 1–3; (4) resolve or re-flag TBVs; (5) upgrade Verification Status only to what the citations actually support; (6) log changes in Notes. Batch size ~10 deals per pass to keep each pass reviewable.

## 6. Track 2 scanner sourcing (daily GitHub Action) — design summary

- **Detection:** EDINET API daily document index filtered to TOB-related document types and large shareholding reports; TDnet disclosure titles; Tier 2 headline scan for foreign-target/outbound deals and rumor-stage items that never touch EDINET.
- **Every detected item** is appended to `Japan_new.csv` with: Record Status (`Confirmed announcement` / `Confirmed proposal (not yet launched)` / `Media report / rumored` / `Update to existing situation`), first-detected date, citations, JA raw + EN translation, and as many master-schema fields as the cited documents support — TBV otherwise.
- **No landmark judgment, no auto-promotion.** Notification email with the dated transformed CSV is sent after each run that produced changes.
