#!/usr/bin/env python3
"""promote_deal.py — promote a Japan_new.csv (scanner) record into Japan_Master.csv
(the landmark knowledge bank). This is the ONLY path from Track 2 -> Track 1.

Usage:
  python pipeline/promote_deal.py JPN-003
  python pipeline/promote_deal.py JPN-003 --yes     # skip interactive confirm

Flow:
  1. Load the named record from data/Japan_new.csv.
  2. Map its fields onto the Japan_Master.csv schema (the two schemas share
     most column names by design; scanner-only metadata columns are dropped;
     Phase-1b columns not present on the scanner record are set to TBV).
  3. Print a full REVIEW of the row that would be added.
  4. On confirmation: assign the next JP-xxx Deal ID, append to
     data/Japan_Master.csv, mark the source record's Record Status as
     "Promoted -> JP-xxx" in Japan_new.csv (append-only ledger — the scanner
     record is never deleted, just annotated), then run transform.py so
     Japan.csv is regenerated in the same operation.
  5. Nothing is pushed to GitHub by this script — publishing is still your
     `git commit && git push` (or the promote-workflow's PR, in CI).

Hard gates (same discipline as intake_agent.py):
  - Citation gate: the record must carry a real Source URL 1 to be promoted.
  - Duplicate check against existing Target+Acquirer pairs in the master.
  - transform.py must succeed after the append, or the run aborts loudly.
"""
import argparse, csv, subprocess, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
MASTER = DATA / "Japan_Master.csv"
NEW = DATA / "Japan_new.csv"

# Japan_new.csv column -> Japan_Master.csv column (identical names omitted;
# only renames/mappings listed here). Scanner-only metadata (Record Status,
# First Detected, Last Updated, Related Master/Watchlist Ref, JA-raw,
# Translation) is intentionally NOT carried onto the master row — it stays
# in Japan_new.csv as the provenance trail.
RENAME = {}  # schemas already share names for shared fields (both derive from
             # the same master column set, per new_deals_data.py / scanner.py)
SCANNER_ONLY = ["Record Status", "First Detected", "Last Updated",
                 "Related Master/Watchlist Ref",
                 "Original Source Title / Excerpt (JA raw)", "Translation (EN)"]


def load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f)), list(csv.DictReader(open(path, encoding="utf-8-sig")).fieldnames)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("record_id", help="Japan_new.csv Record ID, e.g. JPN-003")
    ap.add_argument("--yes", action="store_true", help="skip interactive confirm")
    a = ap.parse_args()

    new_rows, new_cols = load_csv(NEW)
    master_rows, master_cols = load_csv(MASTER)

    src = next((r for r in new_rows if r["Record ID"] == a.record_id), None)
    assert src, f"{a.record_id} not found in Japan_new.csv"
    assert src.get("Source URL 1 (primary)", "").startswith("http"), \
        f"CITATION GATE: {a.record_id} has no primary source URL — cannot promote"

    # build the master-schema row
    row = {c: "TBV" for c in master_cols}
    for c in master_cols:
        if c in SCANNER_ONLY or c == "Deal ID":
            continue
        if c in src and src[c] not in (None, ""):
            row[c] = src[c]

    dupe = [r["Deal ID"] for r in master_rows
            if r["Target Full Name"].strip().lower() == row.get("Target Full Name", "").strip().lower()
            and r["Acquirer Full Name"].strip().lower() == row.get("Acquirer Full Name", "").strip().lower()]
    assert not dupe, f"possible duplicate of existing {dupe} — resolve manually before promoting"

    n = max(int(r["Deal ID"].split("-")[1]) for r in master_rows)
    row["Deal ID"] = f"JP-{n+1:03d}"
    row["Notes / Follow-ups"] = (row.get("Notes / Follow-ups", "") or "") + \
        f" || PROMOTED from Japan_new.csv {a.record_id} via promote_deal.py."

    print("\n" + "=" * 72)
    print(f"PROMOTING {a.record_id} -> {row['Deal ID']}: {row.get('Target Full Name')}")
    print("=" * 72)
    for k in ["Category", "Date Announced", "Acquirer Full Name",
              "Final Offer Price (local)", "Source URL 1 (primary)"]:
        print(f"{k}: {row.get(k)}")
    print("=" * 72)

    if not a.yes:
        if input("Confirm promotion to Japan_Master.csv? [y/N] ").strip().lower() != "y":
            print("Cancelled — no files changed.")
            return 0

    master_rows.append(row)
    with open(MASTER, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=master_cols)
        w.writeheader(); w.writerows(master_rows)

    # annotate (never delete) the scanner-side record
    for r in new_rows:
        if r["Record ID"] == a.record_id:
            r["Record Status"] = f"Promoted -> {row['Deal ID']}"
    with open(NEW, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=new_cols)
        w.writeheader(); w.writerows(new_rows)

    r = subprocess.run([sys.executable, str(Path(__file__).parent / "transform.py"),
                        "--master", str(MASTER), "--outdir", str(DATA)],
                       capture_output=True, text=True)
    print(r.stdout or r.stderr)
    assert r.returncode == 0, "transform.py failed after promotion — inspect before committing"
    print(f"DONE: {row['Deal ID']} added to Japan_Master.csv; Japan.csv regenerated.")
    print("Next: review `git diff`, then commit & push to publish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
