#!/usr/bin/env python3
"""add_deal_cli.py — THE ONE BUTTON, command-line version.

Usage:
  python pipeline/add_deal_cli.py "Kakaku.com EQT LY Bain contest"

Flow (review-before-publish, always):
  1. Wakes the research agent (intake_agent.call_claude): independent research —
     exchange filings first, then Nikkei -> Reuters -> Bloomberg.
  2. Prints a full REVIEW of the proposed row (every field + citations) and
     saves it to data/proposals/proposal_<timestamp>.json. NOTHING is written
     to the master yet.
  3. Asks for approval:
       [y] approve -> appends to data/Japan_Master.csv, runs transform.py
                      (Japan.csv + codebook regenerated), reminds you to
                      git commit/push (publishing stays a human git action).
       [n] reject  -> proposal file kept for reference; master untouched.
  Non-interactive: --approve <proposal.json> applies a previously saved
  proposal after offline review.

Same hard gates as the CI path: citation gate, date parse, duplicate check,
sequential Deal ID, TBV discipline enforced by the agent prompt.
"""
import argparse, csv, datetime, json, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from intake_agent import call_claude  # reuse the same research agent

DATA = Path(__file__).resolve().parent.parent / "data"
MASTER = DATA / "Japan_Master.csv"
PROPOSALS = DATA / "proposals"


def load_master():
    with open(MASTER, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows, list(rows[0].keys())


def validate(row, rows, columns):
    missing = [c for c in columns if c not in row]
    assert not missing, f"agent omitted columns: {missing}"
    row = {c: str(row[c]) for c in columns}
    n = max(int(r["Deal ID"].split("-")[1]) for r in rows)
    row["Deal ID"] = f"JP-{n+1:03d}"
    assert row["Source URL 1 (primary)"].startswith("http"), "CITATION GATE: no primary source"
    assert re.match(r"\d{4}/\d{2}", row["Date Announced"]), f"bad announce date: {row['Date Announced']!r}"
    dupe = [r["Deal ID"] for r in rows
            if r["Target Full Name"].lower() == row["Target Full Name"].lower()
            and r["Acquirer Full Name"].lower() == row["Acquirer Full Name"].lower()]
    assert not dupe, f"possible duplicate of {dupe} — resolve manually"
    return row


def print_review(row):
    print("\n" + "=" * 72)
    print("PROPOSED ROW — REVIEW BEFORE PUBLISH")
    print("=" * 72)
    for k, v in row.items():
        print(f"{k}: {v}")
    print("=" * 72)
    tbv = sum(1 for v in row.values() if "TBV" in str(v))
    print(f"[{tbv} field(s) contain TBV — verify acceptability]\n")


def apply_row(row):
    rows, columns = load_master()
    row = validate(row, rows, columns)  # re-validate against current master
    rows.append(row)
    with open(MASTER, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader(); w.writerows(rows)
    r = subprocess.run([sys.executable, str(Path(__file__).parent / "transform.py"),
                        "--master", str(MASTER), "--outdir", str(DATA)],
                       capture_output=True, text=True)
    print(r.stdout or r.stderr)
    assert r.returncode == 0, "transform.py failed — master change NOT consistent, fix before commit"
    print(f"APPLIED {row['Deal ID']}: {row['Target Full Name']}")
    print("Next: review `git diff`, then commit & push to publish. Nothing is public yet.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mention", nargs="?", help="deal mention to research")
    ap.add_argument("--approve", help="apply a saved proposal json")
    ap.add_argument("--yes", action="store_true", help="skip interactive prompt (still prints review)")
    a = ap.parse_args()

    if a.approve:
        apply_row(json.loads(Path(a.approve).read_text(encoding="utf-8")))
        return 0

    assert a.mention, "provide a deal mention or --approve <file>"
    rows, columns = load_master()
    print(f"Researching independently: {a.mention!r} (filings first; Nikkei->Reuters->Bloomberg) ...")
    row = call_claude(a.mention, columns)
    row = validate(row, rows, columns)

    PROPOSALS.mkdir(exist_ok=True)
    pf = PROPOSALS / f"proposal_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
    pf.write_text(json.dumps(row, ensure_ascii=False, indent=1), encoding="utf-8")
    print_review(row)
    print(f"Proposal saved: {pf}")

    if a.yes:
        apply_row(row); return 0
    ans = input("Approve and apply to Japan_Master.csv? [y/N] ").strip().lower()
    if ans == "y":
        apply_row(row)
    else:
        print("Rejected — master untouched. Proposal kept for reference.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
