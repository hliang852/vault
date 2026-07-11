# Japan M&A Masterfile — Landmark Case Criteria

**Purpose:** records the editorial standard used to select situations for `Japan_Master.csv` (the knowledge bank for case-relations study). This file governs Track 1 only. Track 2 (`Japan_new.csv`, the daily scanner) applies **no** landmark judgment — it records everything in scope and leaves promotion decisions to a human.

**Scope of the knowledge bank:** deals & campaigns announced **2015/01/01 – 2026/06/30** · target or acquirer Japanese · deal size > US$100mn (activist campaigns by stake/impact) · precedent value can override the size floor (recorded case-by-case in Notes).

---

## 1. What "landmark" means here

A landmark case is one that **teaches something transferable**: it set or tested a rule, changed market practice, or is the leading example of a recurring pattern that later deals repeat. The test is pedagogical — *if you removed this case from the study guide, would a practitioner's mental model of Japan special situations be measurably poorer?*

Most deals — even large ones — are not landmarks. Routine agreed TOBs at conventional premiums with clean processes are the base rate, not the curriculum.

## 2. Selection criteria

A situation qualifies if it meets **any one** of the following (most landmarks meet several). The applicable criteria for each deal should be traceable from the Category, Key Debate Points, and Notes columns.

**C1 — Legal / regulatory precedent.** First or defining application of a rule: first triggered poison-pill vote (Toshiba Machine/Murakami 2020); appraisal rulings that moved price (FamilyMart Art. 172); FEFTA "core" review shaping outcome (Yageo/Shibaura; Seven & i core designation); EU FSR first applied to a Japan LBO (Outsourcing/Bain); CFIUS + golden share (Nippon Steel/US Steel); China SAMR as binding constraint (JSR, Shinko); first deals under the amended FIEA TOB regime (eff. 2026/05/01).

**C2 — Market-practice precedent.** Changed how bidders/boards behave: first successful era hostile TOB (Colowide/Ootoya); first blue-chip hostile counter-TOB (HOYA/NuFlare); first competing-TOB price war (Shimachu: DCM vs Nitori); bump wars establishing "bumpology" (Hitachi Kokusai, Benefit One, Fancl, Fuji Soft, Kakaku); contests decided by lock-ups/irrevocables (Fuji Soft, Taiyo); the four-way Unizo auction ending in Japan's first listed-company employee buyout.

**C3 — Governance inflection.** Board vs founder/family/parent conflict, or special-committee conduct that became the reference case for METI 2023 guideline application: Idemitsu/Showa Shell founder opposition; Taisho MBO price criticism; Sogo & Seibu board/labor conflict; Takisawa as the first clean "bona fide offer" acceptance; parent-subsidiary buy-in fairness wave (NTT/Docomo 2020 onward).

**C4 — Activist template.** Campaign that created a repeatable playbook or directly catalyzed M&A: Third Point/Fanuc and /Seven & i (early era); Oasis "Protect Alpine" appraisal playbook; Oasis/Tokyo Dome (campaign → white-knight TOB); Murakami counter-TOB defeating a live MBO (Japan Asia Group); Elliott's balance-sheet campaigns; Effissimo/Toshiba EGM-investigation precedent; Palliser/Keisei (asset-value discount template).

**C5 — Scale or structural significance.** Size alone makes it required study (NTT/Docomo ¥4.25tn; Takeda/Shire; Toshiba/JIP) or the structure is novel (JIC as national-policy buyer; employee buyout; 20+ corporate consortium; JV holding-company merger attempts like Honda/Nissan).

**C6 — Cross-border signal.** Defines feasibility or terms of foreign buyers in Japan (Sharp/Foxconn; Yageo/Shibaura; Couche-Tard/Seven & i) or defines the Japanese outbound pattern and its risks (Takeda/Shire; Japan Post/Toll writedown; Nippon Steel/US Steel politicization; the 2015 outbound insurance wave).

**Cross-cutting inclusion boosters (not sufficient alone):**
- **Recurrence linkage** — same acquirer, target, or fund appearing across multiple cases (Nidec's serial consentless bids; Bain vs KKR repeat matchups; SBI/Shinsei two-stage; Murakami group vehicles). The knowledge bank is explicitly for case-*relations* study, so nodes that create edges are favored.
- **Contested processes** — interlopers, hostile turns, withdrawn recommendations.
- **TSE/METI reform causality** — cases that exist *because of* PBR reform, cross-shareholding unwind, or parent-sub reduction pressure.

## 3. Exclusions

- Routine parent-subsidiary mop-ups and agreed strategic M&A with no frictions, no process novelty, and no recurrence linkage — regardless of size.
- Private-to-private transactions with no public-market lesson (no minority shareholders, no TOB mechanics), unless C1/C6 applies.
- Sub-US$100mn situations unless a criterion clearly overrides (must be stated in Notes).
- Rumor-stage situations — these live in the Watchlist (or `Japan_new.csv` under Track 2) until terms are confirmed by a primary source.

## 4. Row conventions for contests

One row per situation; **one row per bid where the failed/competing bid is itself a landmark** (e.g., Nidec/Makino and MBK/Makino; Couche-Tard/Seven & i and York/Bain). The Competing Bid column must cross-reference the sibling row.

## 5. Promotion and quarantine rules

| From | To | Trigger | Standard |
|---|---|---|---|
| `Japan_Watchlist.csv` | `Japan_Master.csv` | Manual, on confirmed terms | Primary-source citation (Source URL 1) + at least one criterion C1–C6 recorded |
| `Japan_new.csv` (Track 2) | `Japan_Master.csv` | **Manual trigger only** — user names the deal; agent researches and populates a full row | Same as above; never auto-appended |
| Anywhere | Removal | Manual | Situation confirmed out of scope or duplicate |

A manual trigger may be as thin as the mention of a deal name; the population job must then source every field, attach citations, mark unresolved cells TBV, and set Verification Status honestly.

## 6. Verification discipline (unchanged from v1, now with citations)

- Every row carries a **Verification Status** grade; `Medium`/`Low` rows must not be used externally before a verification pass.
- Unverified values are written **TBV**, never invented.
- Every row must carry **Source URL 1** (primary/regulatory where one exists), with Source URL 2–3 for secondary support. See `Japan_Sources_Methodology.md` for the source hierarchy and citation rules.
