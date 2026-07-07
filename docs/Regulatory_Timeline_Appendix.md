# Appendix: Regulatory Timeline (2023–2026H1)

Background for the `timeline_post_meti_2023_guideline`, `timeline_post_tse_reform_2023`, and `timeline_post_fiea_2026_amendment` columns in `data/Japan.csv` (see `Japan_User_Guide.md`'s Regulatory section and `Architecture.md`'s `Japan.csv` schema-changes log). This doc is the "why it matters" reference; the CSV columns are the mechanical yes/no flags derived from it.

Three separate regulatory shifts reshape the incentives and mechanics of every deal in this corpus, depending on which side of each date a deal's `date_announced` falls:

## 1. METI "Guidelines for Corporate Takeovers" — effective 2023-08-31

- **What it is:** Soft law (non-binding, no penalties) issued by Japan's Ministry of Economy, Trade and Industry, titled "Guidelines for Corporate Takeovers – Enhancing Corporate Value and Securing Shareholders' Interests."
- **What changed:** Establishes a board duty to give "sincere consideration" to any **bona fide offer** — one that is specific, has a rationale of purpose, and is feasible — and directs boards not to close off an opportunity with potential shareholder value without good reason. This directly reframes how a target board can justify rejecting, delaying, or defending against an unsolicited approach.
- **Why it matters for this corpus:** it is the operative standard behind every consentless/hostile bid in the dataset (e.g. Takisawa, Brother/Roland DG, AZ-COM/C&F, Nidec/Makino, Yageo) — target boards post-guideline are expected to articulate a specific, principled basis for opposition rather than reflexively rejecting an offer.
- **Column:** `timeline_post_meti_2023_guideline` = `True` if `date_announced >= 2023-08-31`.
- **Source:** [METI press release, 2023-08-31](https://www.meti.go.jp/english/press/2023/0831_001.html); guideline text: [PDF](https://www.meti.go.jp/press/2023/08/20230831003/20230831003-b.pdf).

## 2. TSE "Action to Implement Management that is Conscious of Cost of Capital and Stock Price" — effective 2023-03-31

- **What it is:** A request (not a listing rule with penalties) from the Tokyo Stock Exchange to all Prime and Standard Market listed companies, issued 2023-03-31.
- **What changed:** Targets companies trading below 1x price-to-book (over 40% of listed companies at the time) — asks them to understand their cost of capital, disclose improvement plans, and engage with investors on progress. TSE has since published follow-up disclosure-rate lists (first: 2024-01-15) and continued updates through 2026.
- **Why it matters for this corpus:** low-PBR, capital-inefficient companies are exactly the profile activists and strategic acquirers target — this reform is a standing, market-wide pressure campaign that sits behind much of the activist-campaign and take-private activity in the corpus, independent of any single company's specific facts.
- **Column:** `timeline_post_tse_reform_2023` = `True` if `date_announced >= 2023-03-31`.
- **Source:** [JPX, "Action to Implement Management that is Conscious of Cost of Capital and Stock Price"](https://www.jpx.co.jp/english/equities/follow-up/02.html).

## 3. FIEA Amendment (mandatory tender offer + large shareholding reporting) — effective 2026-05-01

- **What it is:** An amendment to Japan's Financial Instruments and Exchange Act (FIEA), passed by the Diet on 2024-05-15, with the substantive TOB and large-shareholding-reporting changes taking effect 2026-05-01.
- **What changed:**
  - Lowers the mandatory tender offer threshold from 1/3 to **30%** of voting rights (aligning Japan with the more common international 30% standard).
  - Extends the Mandatory Tender Offer requirement to **on-market (on-floor) purchases**, which were previously outside its scope.
  - Updates the Large Shareholder Reporting Rules: clarifies "Purpose of Holding" / "Important Contracts" disclosure items, simplifies joint-holder shareholding calculations, and modernizes the report format.
- **Why it matters for this corpus:** any deal announced on or after 2026-05-01 operates under materially stricter creeping-acquisition and disclosure rules than everything before it — toehold-building strategies that were previously viable via on-market purchases below 1/3 face a lower, more restrictive bar. As of this corpus's cutoff (2026H1), no case is flagged `True` on this column yet — it exists so future additions to the corpus are comparable against a known regime change, not to describe deals that predate it.
- **Column:** `timeline_post_fiea_2026_amendment` = `True` if `date_announced >= 2026-05-01`.
- **Source:** [DLA Piper, "Recent developments on TOB rules and shareholding transparency in Japan" (2026-01)](https://www.dlapiper.com/en-us/insights/publications/2026/01/recent-developments-on-tob-rules-and-shareholding-transparency-in-japan); [Nagashima Ohno & Tsunematsu, "Amendments to the Tender Offer Regulations"](https://www.nagashima.com/en/publications/publication20241213-2/).

## Notes on interpretation

- These are **timing flags, not causal claims**. A deal announced after a given date does not mean that regulation drove its outcome — it means the regime was in force and could plausibly have shaped the parties' behavior. Treat as context for reading a case, not as a feature to explain outcomes statistically (see `Claude.md`: this corpus is not a quant/ML training set).
- These columns are **independent of** the pre-existing `mentions_METI_guidelines` / `mentions_TSE_reform` / `mentions_FIEA` columns, which flag whether a deal's own narrative text explicitly *cites* these regimes. A deal can be timing-eligible (`timeline_post_*` = `True`) without ever mentioning the regime in its notes, and vice versa (e.g. a case's notes referencing "TSE reform pressure" as background context even if the specific PBR-improvement plan predates the deal).
- Not yet wired into `precedent_engine.py`'s similarity score — see `Roadmap.md` Part 2 for how this might factor into cluster/lens design later.
