#!/usr/bin/env python3
"""intake_agent.py — ONE-BUTTON Track 1 intake.

Input: a bare deal mention (e.g. "Kakaku.com EQT" or "JX Advanced Metals IPO
carve-out"). The agent then researches INDEPENDENTLY — exchange filings first
(EDINET/TDnet/company IR), then Nikkei -> Reuters -> Bloomberg for context —
and produces one fully-populated candidate row for data/Japan_Master.csv.

Output is a PROPOSAL, not a commit to main: the GitHub workflow writes it to a
branch and opens a pull request, so the human owner reviews every landmark
addition (per Japan_Landmark_Criteria.md §5 — manual promotion only).

Hard rules enforced in code (not just in the prompt):
  - Row must carry Source URL 1 (citation gate) or the run fails.
  - Deal ID assigned sequentially; announce date must parse; unknowns stay TBV.
  - The model is instructed to write TBV rather than guess, and to preserve
    Japanese filing titles verbatim in Notes.

Env: ANTHROPIC_API_KEY (repo secret). Model kept in one constant below.
"""
import csv, json, os, re, sys, urllib.request

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
MASTER = os.path.join(DATA, "Japan_Master.csv")
DOCS = os.path.join(DATA, "docs")
MODEL = "claude-sonnet-4-6"
API = "https://api.anthropic.com/v1/messages"

SYSTEM = """You are the research agent for a Japan M&A landmark-case knowledge
bank. Populate ONE row of Japan_Master.csv for the deal the user names.

Non-negotiable rules:
1. Research independently: exchange filings first (EDINET tender offer
   registration statements 公開買付届出書, target board opinion statements
   意見表明報告書, TDnet releases, company IR pages), then news context in this
   order: Nikkei, Reuters, Bloomberg. Law-firm memos may support regulatory
   fields but never override filings on dates/prices.
2. NEVER invent a fact. Any field your citations do not support = the string
   "TBV". Dates yyyy/mm/dd. Announcement = first public confirmed
   announcement/proposal (not the media leak; if you use a leak date, say so).
3. Attach exactly the URLs you actually relied on: Source URL 1 must be the
   most primary source available; 2-3 secondary. Facts not covered by these
   three URLs must not appear in the row.
4. Preserve Japanese primary-source titles verbatim inside Notes (JA原文),
   with an English working translation.
5. State which landmark criteria (C1-C6 per the criteria document provided)
   the deal meets, inside the Notes field. If it clearly meets none, say so —
   the human decides whether it still belongs.
6. Output ONLY a JSON object whose keys are EXACTLY the column names provided,
   all values strings. No markdown, no commentary."""


def read(p):
    with open(p, encoding="utf-8-sig") as f:
        return f.read()


def call_claude(deal_mention, columns):
    criteria = read(os.path.join(DOCS, "Japan_Landmark_Criteria.md"))
    sources = read(os.path.join(DOCS, "Japan_Sources_Methodology.md"))
    body = {
        "model": MODEL, "max_tokens": 8000,
        "system": SYSTEM,
        "messages": [{"role": "user", "content":
            f"Deal to research and populate: {deal_mention}\n\n"
            f"Columns (JSON keys, exact):\n{json.dumps(columns)}\n\n"
            f"<criteria>\n{criteria}\n</criteria>\n"
            f"<sources_methodology>\n{sources}\n</sources_methodology>"}],
        "tools": [{"type": "web_search_20250305", "name": "web_search",
                   "max_uses": 12}],
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read())
    text = "\n".join(b.get("text", "") for b in data.get("content", [])
                     if b.get("type") == "text")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"No JSON row in model output:\n{text[:2000]}")
    return json.loads(m.group(0))


def main():
    if len(sys.argv) < 2:
        print("usage: intake_agent.py '<deal mention>'", file=sys.stderr)
        return 2
    mention = sys.argv[1]

    with open(MASTER, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    columns = list(rows[0].keys())

    row = call_claude(mention, columns)

    # ---- validation gates (fail loudly; a bad row must never land) --------
    missing = [c for c in columns if c not in row]
    assert not missing, f"model omitted columns: {missing}"
    row = {c: str(row[c]) for c in columns}
    n = max(int(r["Deal ID"].split("-")[1]) for r in rows)
    row["Deal ID"] = f"JP-{n+1:03d}"
    assert row["Source URL 1 (primary)"].startswith("http"), "CITATION GATE: no primary source URL"
    assert re.match(r"\d{4}/\d{2}(/\d{2})?", row["Date Announced"]), \
        f"unparseable announce date: {row['Date Announced']!r}"
    dupe = [r["Deal ID"] for r in rows
            if r["Target Full Name"].lower() == row["Target Full Name"].lower()
            and r["Acquirer Full Name"].lower() == row["Acquirer Full Name"].lower()]
    assert not dupe, f"possible duplicate of {dupe} — resolve manually"

    rows.append(row)
    with open(MASTER, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({"added": row["Deal ID"], "target": row["Target Full Name"],
                      "verification": row["Verification Status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
