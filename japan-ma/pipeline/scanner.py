#!/usr/bin/env python3
"""scanner.py — Track 2 daily scan (append-only detection -> data/Japan_new.csv).

Sources, per Japan_Sources_Methodology.md:
  1. EDINET API v2 (official, Tier 1): daily document index, filtered by
     Japanese title keywords (公開買付届出書 / 意見表明報告書 / 撤回 / 大量保有報告書).
     Requires EDINET_API_KEY (free registration: https://api.edinet-fsa.go.jp).
  2. TDnet daily disclosure list (Tier 1 content): title-level keyword scan.
     NOTE: no official API — first-run TODO: confirm access method & ToS.
  3. News layer (Tier 2, detection-only): Google News RSS queries scoped to
     Nikkei / Reuters / Bloomberg for foreign-target & rumor-stage items.

Hard rules enforced here:
  - CITATION GATE: no record is appended without at least one source URL.
  - APPEND-ONLY: existing rows are never modified except Last Updated / status
    on a matched open situation ("Update to existing situation").
  - NO landmark judgment, NO auto-promotion to Japan_Master.csv.
  - Japanese titles preserved verbatim in 'Original Source Title / Excerpt (JA raw)';
    machine translation goes to 'Translation (EN)' and is marked as such.
  - Every detected item defaults fields to TBV; only cited facts are written.
"""
import csv, datetime, json, os, re, sys, urllib.parse, urllib.request

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
NEW_CSV = os.path.join(DATA, "Japan_new.csv")

EDINET_ENDPOINT = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
# Title keywords (JA). Deliberately title-based rather than docTypeCode-based to
# avoid hard-coding type codes; VERIFY docTypeCode mapping on first live run and
# tighten if noise is high.
JA_KEYWORDS = ["公開買付届出書", "意見表明報告書", "公開買付撤回届出書",
               "訂正公開買付届出書", "大量保有報告書"]
NEWS_QUERIES = [
    'Japan "tender offer" acquisition',
    'Japan MBO take-private',
    'Japanese company acquisition billion (site:reuters.com OR site:asia.nikkei.com OR site:bloomberg.com)',
]
UA = {"User-Agent": "japan-ma-scanner/1.0 (research; contact repo owner)"}


def http_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def http_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def scan_edinet(date_iso, api_key):
    """Yield (ja_title, filer, doc_url) for in-scope filings on date_iso."""
    url = (f"{EDINET_ENDPOINT}?date={date_iso}&type=2&"
           f"Subscription-Key={urllib.parse.quote(api_key)}")
    try:
        payload = http_json(url)
    except Exception as e:  # network/auth failures must be loud, not silent
        print(f"[edinet] ERROR {date_iso}: {e}", file=sys.stderr)
        return
    for doc in payload.get("results", []):
        title = doc.get("docDescription") or ""
        if any(k in title for k in JA_KEYWORDS):
            doc_id = doc.get("docID", "")
            yield (title, doc.get("filerName", ""),
                   f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?{doc_id}")


def scan_tdnet(date_iso):
    """Title-level scan of the TDnet daily list. TODO(first run): verify URL
    pattern & ToS; consider a licensed feed if scraping is not permitted."""
    ymd = date_iso.replace("-", "")
    url = f"https://www.release.tdnet.info/inbs/I_list_001_{ymd}.html"
    try:
        html = http_text(url)
    except Exception as e:
        print(f"[tdnet] WARN {date_iso}: {e} (skipping)", file=sys.stderr)
        return
    for m in re.finditer(r"<td[^>]*>([^<]*(?:公開買付|ＭＢＯ|MBO|完全子会社化)[^<]*)</td>", html):
        yield (m.group(1).strip(), "", url)


def scan_news():
    """Headline-level RSS detection (Tier 2). Yields (title, source, link)."""
    for q in NEWS_QUERIES:
        url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q)
               + "&hl=en&gl=JP&ceid=JP:en")
        try:
            xml = http_text(url)
        except Exception as e:
            print(f"[news] WARN: {e}", file=sys.stderr)
            continue
        for item in re.findall(r"<item>(.*?)</item>", xml, re.S)[:15]:
            t = re.search(r"<title>(.*?)</title>", item, re.S)
            l = re.search(r"<link>(.*?)</link>", item, re.S)
            if t and l:
                yield (re.sub(r"<!\[CDATA\[|\]\]>", "", t.group(1)).strip(),
                       "Google News RSS", l.group(1).strip())


def load_existing():
    with open(NEW_CSV, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows, (rows[0].keys() if rows else None)


def next_record_id(rows):
    n = max((int(r["Record ID"].split("-")[1]) for r in rows), default=0)
    return f"JPN-{n+1:03d}"


def already_tracked(rows, title, url):
    blob = title + url
    for r in rows:
        for u in ("Source URL 1 (primary)", "Source URL 2", "Source URL 3"):
            if r.get(u) and r[u].split(" ")[0] in blob:
                return True
        if r.get("Original Source Title / Excerpt (JA raw)") and \
           r["Original Source Title / Excerpt (JA raw)"] == title:
            return True
    return False


def make_record(rid, fields, status, title_ja, url, source_label, today):
    rec = {k: "TBV" for k in fields}
    rec.update({
        "Record ID": rid, "Record Status": status,
        "First Detected": today, "Last Updated": today,
        "Related Master/Watchlist Ref": "",
        "Original Source Title / Excerpt (JA raw)": title_ja if re.search(r"[぀-ヿ一-鿿]", title_ja) else "",
        "Translation (EN)": "" if not re.search(r"[぀-ヿ一-鿿]", title_ja) else "(machine translation pending — JA original prevails)",
        "Notes / Follow-ups": f"Auto-detected by scanner ({source_label}) {today}; enrichment pass pending.",
        "Source URL 1 (primary)": url, "Source URL 2": "", "Source URL 3": "",
    })
    if not re.search(r"[぀-ヿ一-鿿]", title_ja):
        rec["Notes / Follow-ups"] = title_ja + " || " + rec["Notes / Follow-ups"]
    return rec


def main():
    today = datetime.date.today().isoformat()
    scan_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    rows, fields = load_existing()
    if fields is None:
        print("Japan_new.csv missing or empty header", file=sys.stderr)
        return 1
    fields = list(fields)
    appended = 0

    detections = []
    api_key = os.environ.get("EDINET_API_KEY", "")
    if api_key:
        detections += [("EDINET", t, u, "Confirmed announcement (filing detected)")
                       for t, _f, u in scan_edinet(scan_date, api_key)]
    else:
        print("[edinet] EDINET_API_KEY not set — skipping Tier 1 scan", file=sys.stderr)
    detections += [("TDnet", t, u, "Confirmed announcement (disclosure detected)")
                   for t, _f, u in scan_tdnet(scan_date)]
    detections += [("News", t, u, "Media report / rumored")
                   for t, _s, u in scan_news()]

    for source_label, title, url, status in detections:
        if not url:            # CITATION GATE
            continue
        if already_tracked(rows, title, url):
            continue
        rec = make_record(next_record_id(rows), fields, status, title, url,
                          source_label, today)
        rows.append(rec)
        appended += 1

    with open(NEW_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # machine-readable output for the workflow (email step TODO reads this)
    print(json.dumps({"date": today, "appended": appended, "total": len(rows)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
