# To-do

Timestamped log of manual verification items and decisions that need the maintainer's attention. Not auto-resolved by any script.

## 2026-07-04

- **Primary-source verification pass** on the 33 rows flagged `Medium - needs verification` and 2 rows flagged `Low - needs verification` in `verification_confidence_code` (confirmed by `output/reports/data_quality.md`, regenerate after any data edit to recheck this count). Cross-check against EDINET tender offer registration statements (公開買付届出書) and TDnet filings before relying on any of these rows in written analysis.
- **`situation_id` linking** -- multi-bid contests (e.g. Seven & i/Couche-Tard vs. York/Bain; Nidec/Makino vs. MBK/Makino) are currently separate, unlinked rows in `data/Japan.csv`. Decide on a field/convention to group rows belonging to the same underlying situation.
- **`precedent_established` field** -- a standardized one-sentence extraction of "what rule/norm this deal is the reference case for," to be pulled from the existing `notes_raw` / `key_debate_points_raw` text (informally present already, not yet structured).
- **Regulatory timeline overlay** -- decide whether/how to plot deal announcement dates against actual rule changes (METI Aug 2023 guidelines, TSE reform, FIEA amendment effective 2026/05/01).
- **Decide on `output/precedent_graph_data.json` -> viewer sync.** The viewer currently needs the JSON manually pasted into `viewer/Japan_Precedent_Constellation.html`'s `const DATA = {...}`. Confirm whether a lightweight build step (Part 3) is worth building now or should wait.
- **High-cardinality raw columns flagged by `output/reports/data_quality.md`**: `category_raw` (90% unique), `industry_raw` (94% unique), `target_ticker_exchange_raw` (95% unique), `acquirer_exchange_raw` (81% unique). No action needed if these are only ever used for lookup/detail (per `docs/Japan_User_Guide.md`) rather than grouping/modeling -- confirm this remains the only usage as the corpus grows.
