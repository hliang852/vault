# Japan M&A Special Situations — Research Database & Pipeline

Two-track system (see `data/docs/Japan_Landmark_Criteria.md` §5):

- **Track 1 — Knowledge bank.** `data/Japan_Master.csv`: curated landmark cases
  (2015/01/01–2026/06/30 scope), 100% primary-source cited, one row per
  situation/bid. Additions ONLY via the one-button intake + human-reviewed PR.
- **Track 2 — Scanner.** `data/Japan_new.csv`: append-only daily detections
  (EDINET + TDnet + news layer), citation-gated, no landmark judgment, rumors
  labeled `Media report / rumored`. Never auto-promoted to the master.

## The one button (Track 1 intake)
Actions tab → **add-deal** → Run workflow → type a deal mention (a name is
enough). The agent researches independently — exchange filings first, then
Nikkei → Reuters → Bloomberg — populates a full master row (TBV where sources
are silent), rebuilds `Japan.csv`, and opens a **pull request** for your
review. Merging the PR is the promotion decision; nothing lands on `main`
without you.

## Daily pipeline (Track 2)
`daily-scan` (07:30 JST): scanner appends new detections → `transform.py`
rebuilds `Japan.csv` + `Japan_Codebook.csv` + dated `output/Japan_YYYY-MM-DD.csv`
→ commit. **Email alert: IMPLEMENTED** — daily scan emails you (with the dated CSV attached)
whenever new situations land. Requires the 5 SMTP secrets per
`data/docs/SMTP_Setup_Guide.md`; run the `test-email` workflow once to verify.
**Auto-transform: IMPLEMENTED** — any push changing `data/Japan_Master.csv`
triggers `transform-on-master-change`, regenerating `Japan.csv` + codebook.

## Downstream (Part 2)
`data/Japan.csv` (+ codebook) is the machine-readable interface for the
analysis / relationship-and-cluster work. `Japan_Master.csv` stays the
human-readable source of truth; `Japan.csv` is always regenerated, never
hand-edited.

## The one button, command-line version
```
python pipeline/add_deal_cli.py "deal mention here"
```
Wakes the research agent (needs ANTHROPIC_API_KEY env var), prints a full
field-by-field REVIEW + saves a proposal file, and only writes to
`Japan_Master.csv` (and reruns transform) after you type `y`. Publishing is
still your `git push`. The GitHub `add-deal` workflow is the cloud twin (PR-based).

## Batch enrichment (Phase 1b) — the efficient route
`enrich` workflow (Actions tab → enrich → Run, set batch size): for each row
with open Phase-1b fields, the agent DOWNLOADS the row's own cited filing PDFs,
extracts advisor / fairness-opinion / min-tender / financing / break-fee /
FEFTA / founder-% / index / IPO-underwriter / mgmt-age / PBR data straight
from the documents (web search only as fallback, ≤6/row), and opens a PR.
Guarantees, enforced in code and verified by test: values name their source
inline; only TBV/'Seeded' cells can be written — verified data can never be
clobbered; transform gates rerun in the same PR; a checkpoint advances so each
run does the next batch. ~11 runs of 10 covers the remaining universe.

## Price enrichment (Phase 1b)
`pipeline/price_enrichment.py` populates T-1/T+1 closes + premiums from a real
price feed once `Filing / First Report Date` is filled — never from memory.

## Setup
1. Private repo. Push these contents.
2. Secrets: `ANTHROPIC_API_KEY` (intake agent), `EDINET_API_KEY`
   (free: https://api.edinet-fsa.go.jp). SMTP secrets later (deferred).
3. First live scanner run: verify TDnet access method/ToS and EDINET keyword
   noise level (flagged TODO in `pipeline/scanner.py`).
4. Standards for any manual edit: `data/docs/Japan_Sources_Methodology.md`
   (citation rules, TBV discipline, JA-raw preservation).

## Files
`pipeline/transform.py` (deterministic encoder, integrity gates: unique IDs,
announce dates present, 100% citation coverage) · `pipeline/scanner.py` ·
`pipeline/intake_agent.py` · `pipeline/send_notification.py` (stub) ·
workflows: `daily_scan` / `add_deal` / `test_pipeline`.
