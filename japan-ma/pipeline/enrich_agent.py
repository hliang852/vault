#!/usr/bin/env python3
"""enrich_agent.py — efficient Phase-1b enrichment (runs in GitHub Actions / locally).

Why this exists: advisor, fairness-opinion, min-tender, financing, break-fee,
FEFTA, founder-%, index-membership, IPO-underwriter, management-age and PBR
data mostly live INSIDE the TOB-filing PDFs each row already cites — search
snippets never surface them. So instead of one manual search per deal, this
agent, for each row with TBV target fields:

  1. downloads the row's cited Source URL 1-3 (PDFs or HTML, ≤20MB each),
  2. sends the documents + the row's existing verified context to Claude with
     a strict extraction prompt: fill ONLY what the documents state; if the
     documents are silent, the agent may use web_search (≤6 uses) with the
     established query patterns; anything unverified stays "TBV",
  3. collects a JSON patch per row with per-field evidence notes,
  4. writes ALL patches to data/proposals/enrichment_<ts>.json + a human-readable
     review file. NOTHING touches the master in propose mode.

Apply mode (`--apply <file>`) merges reviewed patches into Japan_Master.csv
(only TBV cells are overwritten — verified data is never clobbered) and reruns
transform.py. In CI, the enrich workflow opens a PULL REQUEST with the applied
patch, so review-before-publish is preserved.

Usage:
  python pipeline/enrich_agent.py --limit 10                 # propose batch
  python pipeline/enrich_agent.py --limit 10 --auto-apply    # CI: apply -> PR review
  python pipeline/enrich_agent.py --apply data/proposals/enrichment_x.json
Env: ANTHROPIC_API_KEY. Checkpoint: data/proposals/enrich_done.txt (deal IDs
already processed; delete a line to reprocess).
"""
import argparse, base64, csv, datetime, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
MASTER = DATA / "Japan_Master.csv"
PROPOSALS = DATA / "proposals"
CHECKPOINT = PROPOSALS / "enrich_done.txt"
API = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"
UA = {"User-Agent": "japan-ma-enrich/1.0 (research)"}

FIELDS = [
    "Fairness Opinion Provider", "Financial Advisor (Target)",
    "Financial Advisor (Acquirer)", "Min Tender Condition (Y/N)",
    "Min Tender Condition Detail", "Financing Description",
    "Break Fee (Y/N)", "Break Fee Amount", "FEFTA Classification",
    "Founder/Family Ownership %", "Index Membership",
    "Target IPO Lead Underwriter", "Key Management Age at Announcement",
    "PBR at Announcement",
]

SYSTEM = """You extract deal-process data for a Japan M&A knowledge bank.
You are given (a) a deal row's verified context and (b) its cited primary
documents. Fill ONLY the requested fields.

Rules — absolute:
1. A value must be supported by the attached documents, or (only if documents
   are silent) by a web search you actually ran; name the source in the value
   itself, e.g. "SMBC Nikko (target FA & valuer; per TOB registration p.X)" or
   "... (per MarketScreener deal record)".
2. If you cannot support a field, output exactly "TBV". Never infer, never
   recall from memory, never copy from a DIFFERENT deal's filing.
3. Activist campaigns / failed proposals: process fields are often legitimately
   "n/a (campaign — no tender process)"; use that, not TBV, where structurally true.
4. Seeded values marked 'Seeded from cited row text' may be REPLACED with
   richer document-based detail; values without TBV/Seeded markers are verified
   — return "KEEP" for those.
5. Output ONLY a JSON object: {"fields": {<field name>: <value>}, "confidence_notes": "<1-2 lines>"}."""


def fetch_doc(url):
    """Download a cited document; return an API content block or None."""
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read(20_000_000)
            ctype = r.headers.get("Content-Type", "")
    except Exception as e:
        print(f"    fetch failed {url[:80]}: {e}", file=sys.stderr)
        return None
    if url.lower().endswith(".pdf") or "pdf" in ctype:
        return {"type": "document", "source": {"type": "base64",
                "media_type": "application/pdf",
                "data": base64.b64encode(raw).decode()}}
    text = re.sub(r"<[^>]+>", " ", raw.decode("utf-8", errors="replace"))
    text = re.sub(r"\s+", " ", text)[:60_000]
    return {"type": "text", "text": f"[Fetched from {url}]\n{text}"}


def call_claude(row, docs):
    context = {k: row[k] for k in [
        "Deal ID", "Category", "Date Announced", "Target Full Name",
        "Acquirer Full Name", "Deal Structure", "Final Offer Price (local)",
        "Notes / Follow-ups"] if k in row}
    current = {f: row.get(f, "TBV") for f in FIELDS}
    content = docs + [{"type": "text", "text":
        f"Deal context (verified):\n{json.dumps(context, ensure_ascii=False)}\n\n"
        f"Current field values (fill TBV ones; KEEP verified ones):\n"
        f"{json.dumps(current, ensure_ascii=False)}\n\nFields to output: {json.dumps(FIELDS)}"}]
    body = {"model": MODEL, "max_tokens": 3000, "system": SYSTEM,
            "messages": [{"role": "user", "content": content}],
            "tools": [{"type": "web_search_20250305", "name": "web_search",
                       "max_uses": 6}]}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=900) as r:
        data = json.loads(r.read())
    text = "\n".join(b.get("text", "") for b in data.get("content", [])
                     if b.get("type") == "text")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in response: {text[:500]}")
    return json.loads(m.group(0))


def load_master():
    with open(MASTER, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows, list(rows[0].keys())


def needs_enrichment(row):
    return any(str(row.get(f, "")).strip().upper().startswith("TBV") or
               "Seeded from cited row text" in str(row.get(f, "")) for f in FIELDS)


def propose(limit):
    rows, _ = load_master()
    done = set(CHECKPOINT.read_text().split()) if CHECKPOINT.exists() else set()
    patches, processed = {}, []
    for row in rows:
        if len(patches) >= limit:
            break
        did = row["Deal ID"]
        if did in done or not needs_enrichment(row):
            continue
        print(f"[{did}] {row['Target Full Name'][:40]} — fetching cited docs...")
        docs = []
        for c in ("Source URL 1 (primary)", "Source URL 2", "Source URL 3"):
            m = re.search(r"https?://\S+", str(row.get(c, "")))
            if m:
                d = fetch_doc(m.group(0).rstrip(")"))
                if d:
                    docs.append(d)
        try:
            result = call_claude(row, docs)
            fields = {k: v for k, v in result.get("fields", {}).items()
                      if k in FIELDS and v not in ("KEEP", "", None)}
            patches[did] = {"fields": fields,
                            "confidence_notes": result.get("confidence_notes", ""),
                            "n_docs": len(docs)}
            filled = sum(1 for v in fields.values() if v != "TBV")
            print(f"    -> {filled} field(s) supported ({len(docs)} docs)")
        except Exception as e:
            print(f"    ERROR {did}: {e}", file=sys.stderr)
        processed.append(did)

    PROPOSALS.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pf = PROPOSALS / f"enrichment_{ts}.json"
    pf.write_text(json.dumps(patches, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(CHECKPOINT, "a") as f:
        f.write("\n".join(processed) + "\n")
    # human-readable review file
    rv = PROPOSALS / f"enrichment_{ts}_REVIEW.txt"
    with open(rv, "w", encoding="utf-8") as f:
        for did, p in patches.items():
            f.write(f"=== {did} ({p['n_docs']} docs) — {p['confidence_notes']}\n")
            for k, v in p["fields"].items():
                f.write(f"  {k}: {v}\n")
    print(f"\nProposed {len(patches)} row-patches -> {pf}\nReview file -> {rv}")
    return pf


def apply(path):
    patches = json.loads(Path(path).read_text(encoding="utf-8"))
    rows, cols = load_master()
    changed = 0
    for row in rows:
        p = patches.get(row["Deal ID"])
        if not p:
            continue
        for k, v in p["fields"].items():
            cur = str(row.get(k, ""))
            if cur.strip().upper().startswith("TBV") or "Seeded from cited row text" in cur:
                if v != "TBV":
                    row[k] = v
                    changed += 1
    with open(MASTER, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(rows)
    r = subprocess.run([sys.executable, str(Path(__file__).parent / "transform.py"),
                        "--master", str(MASTER), "--outdir", str(DATA)],
                       capture_output=True, text=True)
    print(r.stdout or r.stderr)
    assert r.returncode == 0, "transform failed after patch — inspect before commit"
    print(f"Applied {changed} field update(s). Review `git diff`, then commit (PR in CI).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--apply", help="apply a reviewed proposal json")
    ap.add_argument("--auto-apply", action="store_true",
                    help="CI mode: propose then apply immediately (PR is the review gate)")
    a = ap.parse_args()
    if a.apply:
        apply(a.apply); return 0
    pf = propose(a.limit)
    if a.auto_apply:
        apply(pf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
