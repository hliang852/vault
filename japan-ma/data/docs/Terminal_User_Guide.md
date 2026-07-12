# Japan M&A Pipeline — Terminal User Guide

Everything below runs from your repo root after `cd ~/vault/japan-ma` (adjust
path to wherever your clone lives). Two ways to trigger each action: locally
via these commands, or remotely via the GitHub Actions tab (same underlying
scripts) — use whichever you have open.

---

## 1. Add a brand-new deal (independent research from scratch)

Use this when you've heard of a deal that ISN'T sitting in `Japan_new.csv` yet
— you're naming it fresh and want the agent to research it end-to-end.

```bash
cd ~/vault/japan-ma
export ANTHROPIC_API_KEY=sk-ant-...      # only needed once per terminal session
python pipeline/add_deal_cli.py "Kakaku.com EQT LY Bain contest"
```

**What happens:**
1. The agent researches independently — exchange filings first (EDINET/TDnet/company IR), then Nikkei → Reuters → Bloomberg for context.
2. It prints a **full field-by-field review** of the proposed row to your terminal and saves it to `data/proposals/proposal_<timestamp>.json`. **Nothing is written yet.**
3. It asks: `Approve and apply to Japan_Master.csv? [y/N]`
   - Type `y` → the row is appended, `Japan.csv` + `masterfile.xlsx` are regenerated automatically, and you'll see `APPLIED JP-108: ...`
   - Type anything else (or just Enter) → nothing is touched; the proposal file stays for later reference.
4. **Publishing is still a separate step** — review `git diff`, then:
   ```bash
   git add data/
   git commit -m "Add [deal name]"
   git push
   ```

**Remote equivalent:** GitHub → Actions tab → `japan-ma-add-deal` → Run workflow → type the deal mention → it opens a **pull request** for you to review and merge instead of prompting in a terminal.

---

## 2. Promote a scanner-detected deal to the knowledge bank

Use this when the **daily scanner** already found something (it's sitting in
`Japan_new.csv` with an ID like `JPN-005`) and you've decided it belongs in
the permanent landmark file.

First, see what's waiting:
```bash
open data/Japan_new.csv        # or: python -c "import pandas as pd; print(pd.read_csv('data/Japan_new.csv')[['Record ID','Record Status','Target Full Name']])"
```

Then promote the one you want:
```bash
python pipeline/promote_deal.py JPN-005
```

**What happens:**
1. Prints a review of the row as it will appear in `Japan_Master.csv`.
2. Asks for confirmation (`[y/N]`) — same pattern as above.
3. On yes: appends to `Japan_Master.csv`, regenerates `Japan.csv` + `masterfile.xlsx`, and marks the original `Japan_new.csv` record as `Promoted -> JP-xxx` (it's never deleted — the scanner record stays as a permanent provenance trail).
4. Same publish step: `git add data/ && git commit -m "Promote JPN-005" && git push`

To skip the interactive prompt (e.g. scripting it): add `--yes`.

**Remote equivalent:** Actions tab → `japan-ma-promote` → Run workflow → type the Record ID (e.g. `JPN-005`) → opens a PR for review/merge.

---

## 3. Check what the daily scanner found (no action needed — it runs itself)

The scanner runs automatically every day at 07:30 JST. It **only** appends to
`Japan_new.csv` — it never touches `Japan_Master.csv` or `Japan.csv`. When it
finds something, you'll get an email with that day's new-records CSV attached.
You don't need to do anything unless you want to promote one (see #2) — the
scanner's job is detection and alerting, not deciding what's a landmark.

To run it manually instead of waiting for the schedule:
```bash
python pipeline/scanner.py
```
(Needs `EDINET_API_KEY` set as an environment variable to hit the Tier-1 feed;
runs with reduced coverage — news-layer only — if not set.)

**Remote equivalent:** Actions tab → `japan-ma-daily-scan` → Run workflow.

---

## 4. Rebuild Japan.csv manually (rarely needed — it's automatic)

`Japan.csv` and `masterfile.xlsx` regenerate automatically the moment
`Japan_Master.csv` changes (via `add_deal_cli.py`, `promote_deal.py`, or a
manual edit + push, which triggers the `japan-ma-transform-on-master-change`
workflow). You only need this if you've hand-edited the master and want to
check the result locally before pushing:

```bash
pip install pandas openpyxl   # once
python pipeline/transform.py --master data/Japan_Master.csv --outdir data
```

---

## 5. Enrich existing rows with missing fields (advisors, fairness opinions, etc.)

This is the batch job that fills in Phase-1b columns (financial advisors,
fairness opinions, financing terms, etc.) by fetching each row's own cited
filings.

```bash
python pipeline/enrich_agent.py --limit 10
```
Prints a review file to `data/proposals/enrichment_<timestamp>_REVIEW.txt`.
Nothing is applied automatically unless you add `--auto-apply`:
```bash
python pipeline/enrich_agent.py --limit 10 --auto-apply
```
(Only ever overwrites cells that are still `TBV` or marked `Seeded` — verified
data can never be clobbered, by design.)

**Remote equivalent:** Actions tab → `japan-ma-enrich` → Run workflow → set batch size → opens a PR.

---

## Quick reference

| I want to... | Command |
|---|---|
| Add a deal I know about, not yet detected | `python pipeline/add_deal_cli.py "<mention>"` |
| Promote a scanner-detected deal | `python pipeline/promote_deal.py JPN-xxx` |
| See what the scanner found today | check email, or `cat data/Japan_new.csv` |
| Force a scan right now | `python pipeline/scanner.py` |
| Force a rebuild of Japan.csv/xlsx | `python pipeline/transform.py --master data/Japan_Master.csv --outdir data` |
| Fill in missing advisor/fairness/etc. data | `python pipeline/enrich_agent.py --limit 10 --auto-apply` |
| Publish any of the above | `git add data/ && git commit -m "..." && git push` |

**One rule that never changes:** `Japan.csv` is never hand-edited — it's always the regenerated output of `Japan_Master.csv`. If they ever look out of sync, just rerun step 4.
