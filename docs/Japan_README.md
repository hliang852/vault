# Japan M&A, Takeovers & Special Situations — Masterfile (Phase 1 of 2)

**Scope:** deals & campaigns announced 2023/01/01 – 2026/06/30 · Target or acquirer Japanese · Deal size > US$100mn (activist campaigns included by stake/impact) · Compiled 2026/07/03

---

## 1. What this file set is

A structured masterfile of Japanese TOBs, MBOs, take-privates, hostile/unsolicited takeovers, cross-border M&A and activist campaigns. This is **Phase 1** (the data spine). **Phase 2** — the PDF study guide with executive summaries, per-deal regulatory tables, vertical timelines and price charts — will be built on top of this table once the flagged fields are locked down.

**Files:**

| File | Contents |
|---|---|
| `README_Japan_MA_Masterfile.md` | This document — methodology, conventions, field dictionary, regulatory map |
| `Japan_MA_Masterfile_2023-2026H1.csv` | The structured table: 62 situations, one row per situation (contests shown as one row per bid where the failed bid is itself a landmark, e.g., Nidec/Makino vs MBK/Makino; Couche-Tard/Seven & i vs York/Bain) |
| `Japan_MA_Watchlist_Rumored.csv` | Situations not yet promotable to the masterfile (rumor-stage or unverified terms) |

CSVs are UTF-8 with BOM (opens cleanly in Excel with Japanese characters intact).

## 2. Honest limitations — read before relying on this

**(a) Coverage.** Japan recorded ~5,100 M&A transactions in 2025 alone (RECOF). A literally complete >$100mn universe over 3.5 years is several hundred rows and requires a licensed database (Bloomberg `MA<GO>`, LSEG/Refinitiv, Mergermarket, MARR/RECOF, SPEEDA). This file covers the ~60 most significant and precedent-setting situations across every requested category — the ones any special-situations study guide must include — and is built to be extended.

**(b) Verification.** Cells marked **TBV** are best-recollection estimates or approximations that MUST be verified against primary sources (TDnet filings, EDINET tender offer registration statements 公開買付届出書, target board opinion statements 意見表明報告書, press releases) before external use. The **Verification Status** column grades each row:

- `Verified via search (Jul 2026)` — checked against current sources at compilation
- `High confidence` — extensively documented public record
- `Medium` / `Low` — verify dates, prices, premiums before use

**(c) Price data.** Unaffected prices and premiums are the most error-prone fields from memory; where I was not confident the cell says TBV rather than a fabricated number. Phase 2 price charts require a proper price feed (e.g., TSE/exchange data) — charts will not be drawn from invented prices.

## 3. Conventions

- **Dates:** `yyyy/mm/dd`. Announcement = first public announcement/confirmed proposal (activist campaigns: first public disclosure or campaign launch). Completion = squeeze-out/settlement or delisting where noted; Failure = withdrawal/termination date.
- **Time to close:** months, computed as (completion − announcement)/30.44, one decimal.
- **FX:** US$ figures as reported at announcement where available; otherwise ≈¥145–155/US$ period rates.
- **Deal size:** equity value of shares acquired unless noted EV. Activist campaign rows use stake value in the size columns and n/a in offer-price fields.

## 4. Field dictionary — practitioner additions (beyond the requested fields)

- **Final vs Initial Offer Price + bump count** — bump frequency is now the single most tradeable Japan special-sits statistic (Fancl, Benefit One, Shibaura, Fuji Soft).
- **Special Committee (Y/N)** — post-METI-2023-guidelines, committee process quality drives both deal certainty and appraisal risk.
- **Competing Bid / Interloper** — interloper risk is the defining feature of the 2024–26 market; needed for base-rate analysis.
- **Toehold / Irrevocables / Tender Agreements** — lock-ups decided Fuji Soft (3D+Farallon ~33% to KKR) and Taiyo (42.2% to KKR); essential field.
- **Squeeze-out Mechanism** — share consolidation vs demand for cash-out determines the appraisal route (Companies Act Art. 172 vs Art. 179-8).
- **Delisting Date** — the true end of an arb position (borrow, index flows).
- **Verification Status + Notes** — data hygiene.

**Recommended Phase 1b additions** (not yet populated): premium to 1M/3M VWAP (standard in Japanese fairness analyses, less noisy than spot); minimum tender condition & majority-of-minority condition (Y/N); fairness opinion provider & financial/legal advisors; FEFTA classification (core / designated / none); appraisal & litigation docket (Art. 172 petitions — Taisho, JSR etc.); financing (LBO lenders / preferred structures); break fee (rare but emerging); TSE market segment & index membership (TOPIX/Nikkei removal flows); founder/family ownership %; PBR at announcement (the TSE-reform metric).

## 5. Regulatory map used in the "Rules" column

- **FIEA (Financial Instruments & Exchange Act) TOB rules** — note the amended mandatory-TOB regime effective **2026/05/01** (threshold lowered to 30%, on-market purchases captured; large-shareholding reporting also amended), which reshapes every deal announced after that date.
- **FEFTA (Foreign Exchange & Foreign Trade Act)** inward FDI screening — "core designated business" review was decisive in Yageo/Shibaura (~7-month review, cleared with conditions) and framed Seven & i/Couche-Tard (core designation Sep 2024).
- **METI Corporate Takeover Guidelines (Aug 2023)** — "bona fide offer" duty to consider; governs consentless bids (Takisawa, Brother/Roland DG, AZ-COM/C&F, Nidec/Makino, Yageo).
- **Companies Act** — squeeze-outs, appraisal (Art. 172), EGMs, share exchanges.
- **JFTC (Anti-Monopoly Act) + foreign merger control** — China SAMR was the binding constraint on JSR and Shinko; the EU Foreign Subsidies Regulation first bit a Japan LBO in Outsourcing/Bain.
- **Sector regimes** — Banking Act (Shinsei), Broadcast Act foreign caps (Fuji Media), insurance change-of-control (Nippon Life, Sompo, Meiji Yasuda), CFIUS/DPA §721 + golden share (Nippon Steel/US Steel).

## 6. Phase 2 (not executed yet, per instruction)

PDF study guide: per-deal executive summaries; regulatory-steps table (steps → triggering rules → debate points → activist involvement → resolution); annotated vertical timelines (date / event / stock move); pre-event-to-post-mortem price charts.

**Prerequisites:** sign-off on the deal universe; resolution of TBV cells (targeted verification passes deal-by-deal); a price-data source for the charts.
