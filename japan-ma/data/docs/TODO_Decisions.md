# Japan M&A Project — TO-DO / Decision List (updated 2026/07/12)

## ⚠️ FRONT-AND-CENTER: Owner review needed on deferred items

**APPROVED (resolved, confirmed correct by owner 2026/07/12):**
- JP-031 MBK/Makino — Blocked (FEFTA stop recommendation stood past 2026/05/01 deadline)
- JP-062 MCJ — Concluded (TOB result after 2026/03/24 close, ¥2,200, Maven/Ascender opposition documented)
- Kakaku.com (Japan_new JPN-001/002) — still genuinely open as of 2026/07/12 (EQT deadline 2026/07/16 imminent; LY/Bain not yet launched, expected ~Sept 2026 pending board support). Will resolve itself in the next few weeks — re-check after 07/16.

**DEFERRED — needs owner decision on priority / whether to pursue further (carried from 2026/07/06, still open):**
1. Yageo/Shibaura (JP-044) exact delisting date
2. T-Gaia (JP-029) exact delisting date
3. Fancl (JP-023) exact delisting date
4. Roland DG (JP-020) exact delisting date
5. Outsourcing (JP-009) exact delisting date
6. Infocom (JP-025) exact delisting date
7. SCSK (JP-051) exact delisting date
8. Elliott/SoftBank (JP-037) precise 2024 disclosure date & stake
9. Exedy/Murakami (JP-039) stake %
10. Fuji Media (JP-055) Dalton-specific proposals
11. Elliott/Sumitomo (JP-036) response quantum
12. Taisho (JP-007) appraisal docket outcome
13. Mitsubishi Tanabe (JP-040) exact closing date
14. Ampere (JP-048) exact closing date
15. Toyota Industries (JP-043) squeeze-out completion + TMC self-tender confirmation
16. NSG (JP-059) June AGM result
17. Taiyo (JP-060) TOB result

**RESOLVED 2026/07/12 — three new deals added (universe now 110 rows):**
- **JP-108 Descente full privatization** (Itochu/BS Investment, ¥4,350, delisted 2025/01/24) — completes the arc begun by JP-078 (2019 hostile partial TOB). SC rejected ¥3,800, demanded ¥4,600, extracted ¥4,350.
- **JP-109 Itochu-Shokuhin** (¥13,000, delisted 2026/05/19) — activist-catalyzed; lowball ¥9,611 opening (3.34% premium) → ¥13,000 (+35%) after a US activist fund's letter leaked and moved the stock 16% in a day. Uses the Companies Act **Art. 179 cash-out** route (≥90%), not share consolidation. **FOLLOW-UP: identify the activist fund (unnamed in sources).**
- **JP-110 FDK / Silitech (the "Fujitsu-adjacent" deal)** — Taiwanese acquirer takes 45% via a **partial TOB with a purchase cap**: Fujitsu tenders all 58.82% but only 45% can be bought, so it deliberately retains a residual stake + brand license. Contains an explicit **contractual counter-TOB carve-out** (≥3% superior bid, ≥5 bd before deadline). BELOW the $100mn floor (≈¥6.8bn) — retained under the precedent-value override. Completes the **Fujitsu portfolio-transformation family** with Shinko Electric (JP-010) and Fujitsu General (JP-056). **FOLLOW-UP: TOB result, completion date, premium, FEFTA classification.**

---

## Status by section

### A. Data-quality follow-ups
- **A1 (flagged-TBV resolution):** ✅ DONE — 3 time-ripe items resolved 2026/07/06 (see APPROVED above)
- **A2 (Japanese primary-source layer):** 🔶 IN PROGRESS, NOT DONE — citations are overwhelmingly English-language (IR releases, Reuters/Bloomberg, law-firm pages); very few are the actual EDINET JA filing. Attaching verbatim 公開買付届出書/意見表明報告書 titles requires a dedicated EDINET search per deal (~100 more searches, different research mode than advisor/fairness work). Continuing incrementally; will report real counts, not claim completion prematurely.
- **A3 (announce-date convention / leak-vs-formal basis):** ✅ DONE 2026/07/12 — `date_announced_basis` column added to Japan_Master.csv (107/107 populated: 93 formal, 8 documented leak-basis, 6 approximate/campaign)

### B. Regeneration of derived files
✅ DONE and ongoing — `transform.py` regenerates `Japan.csv` + `Japan_Codebook.csv` + **`masterfile.xlsx`** (added 2026/07/12, formatted Excel mirror, auto-sized columns, frozen header) every time `Japan_Master.csv` changes. Never hand-edited. Auto-triggered by `japan-ma-transform-on-master-change` workflow.

### C. Scope expansion 2015-2022
✅ DONE — C1 (2015 cohort, 7 deals) · C2 (2016-17, 7 of 8 — Accordia Golf excluded per Y/N vote) · C3 (2018-19, 10 deals across 3 batches) · C4 (2020, 8 of 10 — Maeda Road excluded, Invesco/Starwood added separately as JP-102) · C5 (2021-22, 6 deals). Plus universe lock-in (2026/07/06): 7 owner-approved add-ons (JP-101–107). **Total: 107 rows, 100% cited.**

### D. GitHub Actions pipeline
✅ Repo scaffolded, private, secrets configured (owner-confirmed 2026/07/12) · email tested and working · **architecture corrected 2026/07/12**:
- `japan-ma-daily_scan.yml`: scanner appends ONLY to `Japan_new.csv`; produces dated snapshot `output/Japan_new_YYYY-MM-DD.csv`; emails that attachment. **No longer touches Japan_Master.csv or Japan.csv.**
- **NEW `pipeline/promote_deal.py` + `japan-ma-promote.yml` workflow**: the only path from Track 2 → Track 1. `python pipeline/promote_deal.py JPN-xxx` (or the Actions "promote" workflow) maps a scanner record onto the master schema, appends it, and regenerates Japan.csv in the same operation.
- `japan-ma-transform_on_change.yml`: unchanged trigger (fires only on Japan_Master.csv commits — i.e., only after a promotion), now also emits masterfile.xlsx.
- `japan-ma-add_deal.yml` / `add_deal_cli.py`: unchanged — independent research for a NAMED deal not yet in Japan_new.csv.
- **Terminal user guide**: see companion doc `Terminal_User_Guide.md`.

### E. Phase 1b schema enrichment (owner: action all items)
🔶 IN PROGRESS. Coverage as of 2026/07/12 (of 107 rows): Min Tender Condition 49 · Index Membership 76 · FA(Acquirer) 40 · FA(Target) 36 · Min Tender Detail 48 · Fairness Opinion 30 · Break Fee 20 · IPO Underwriter 17 · FEFTA 12 · Founder/Family % 7 · **PBR 1 · Management Age 0** (structurally blocked — need BVPS/financial-statement source and executive-bio source respectively, not deal press; recommend a licensed data feed or the enrich_agent's PDF-fetch route rather than further web search for these two). Continuing in batches; will report "Done" only when genuinely exhausted or blocked on a structural data-source gap.

### F. Case-relations graph
⏸ WAITING for explicit request, per owner instruction (after C and E complete).

### G. Phase 2 PDF study guide
⏸ WAITING for explicit request, per owner instruction (after F complete).

### H. Watchlist refresh
⏸ WAITING — last step, after D fully settles.
