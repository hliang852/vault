#!/usr/bin/env python3
"""price_enrichment.py — populate Pre/Post-Event closes and premiums from a REAL price feed.

Per project rule (README §2c): price fields must come from a price feed, never
from model memory. This script runs where network is open (GitHub Actions or
your machine), NOT inside the chat sandbox.

For each row with a day-precision "Filing / First Report Date" and a numeric
JP ticker, it:
  1. fetches daily OHLC from Stooq's free CSV endpoint
     (https://stooq.com/q/d/l/?s={ticker}.jp&i=d) — VERIFY Stooq ToS/coverage on
     first run; swap FEED_URL for a licensed feed if preferred,
  2. finds the last trading close STRICTLY BEFORE the recorded date (T-1) and
     the first trading close STRICTLY AFTER it (T+1),
  3. writes both closes, Premium to T-1 (final offer price vs T-1), and Market
     Reaction T+1 ((T+1/T-1)-1), tagging each value "per Stooq {date}" so the
     source is auditable,
  4. touches ONLY rows where the three inputs (date, ticker, numeric offer)
     exist — everything else stays TBV. Fails loudly per ticker; a summary of
     failures prints at the end and exits non-zero if nothing succeeded.

Usage: python pipeline/price_enrichment.py [--master data/Japan_Master.csv] [--dry-run]
Note: "Filing / First Report Date" must be populated first (enrichment pass /
intake agent); PBR additionally needs BVPS from financial statements — out of
scope here, tracked in TODO.
"""
import argparse, csv, datetime, io, re, sys, time, urllib.request

FEED_URL = "https://stooq.com/q/d/l/?s={sym}&i=d"
UA = {"User-Agent": "japan-ma-price-enrichment/1.0"}


def fetch_daily(sym):
    req = urllib.request.Request(FEED_URL.format(sym=sym), headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode()
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "Close" not in rows[0]:
        raise ValueError(f"no data for {sym}")
    return [(datetime.date.fromisoformat(x["Date"]), float(x["Close"])) for x in rows if x.get("Close")]


def parse_date(s):
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", str(s))
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def first_number(s):
    m = re.search(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", str(s))
    return float(m.group(0).replace(",", "")) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="data/Japan_Master.csv")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    with open(a.master, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    ok = fail = skip = 0

    for r in rows:
        d = parse_date(r.get("Filing / First Report Date", ""))
        tk = re.search(r"\b(\d{4})\b", r.get("Target Ticker / Exchange", ""))
        offer = first_number(r.get("Final Offer Price (local)", ""))
        if not (d and tk and offer) or "¥" not in str(r.get("Final Offer Price (local)", "")):
            skip += 1
            continue
        if str(r.get("Pre-Event Close (T-1, local)", "")).upper() not in ("TBV", ""):
            skip += 1
            continue
        sym = f"{tk.group(1)}.jp"
        try:
            series = fetch_daily(sym)
            pre = max(((dt, c) for dt, c in series if dt < d), key=lambda x: x[0])
            post = min(((dt, c) for dt, c in series if dt > d), key=lambda x: x[0])
            r["Pre-Event Close (T-1, local)"] = f"¥{pre[1]:,.1f} ({pre[0]}, per Stooq)"
            r["Post-Event Close (T+1, local)"] = f"¥{post[1]:,.1f} ({post[0]}, per Stooq)"
            r["Premium to T-1 Close (%)"] = f"{(offer/pre[1]-1)*100:+.1f}% (offer {offer:,.0f} vs T-1, per Stooq)"
            r["Market Reaction T+1 (%)"] = f"{(post[1]/pre[1]-1)*100:+.1f}% (per Stooq)"
            ok += 1
        except Exception as e:
            print(f"[{r['Deal ID']}] {sym}: FAILED {e}", file=sys.stderr)
            fail += 1
        time.sleep(1.0)  # be polite to the feed

    print(f"price_enrichment: populated {ok}, failed {fail}, skipped {skip} "
          f"(skips = missing date/ticker/JPY-offer or already populated)")
    if a.dry_run:
        return 0
    if ok:
        with open(a.master, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(rows)
    return 0 if ok or skip else 1


if __name__ == "__main__":
    sys.exit(main())
