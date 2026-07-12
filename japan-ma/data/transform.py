#!/usr/bin/env python3
"""transform.py — Japan_Master.csv -> Japan.csv (ML-ready) + Japan_Codebook.csv

Deterministic re-implementation of the documented encoding (Japan_User_Guide.md),
extended with source_url_1/2/3 (v2 citation columns). No new facts are created:
every output value is copied from the master or mechanically derived from it.

Usage:
  python transform.py --master Japan_Master.csv --outdir . [--dated]
  (--dated additionally writes Japan_YYYY-MM-DD.csv for the notification pipeline)
"""
import argparse, csv, datetime, re, sys
import pandas as pd

HEDGE = re.compile(r"TBV|≈|~|approx|expected|reported range|estimated|TBD", re.I)

def is_est(s):
    return bool(s) and bool(HEDGE.search(str(s)))

def txt(v):
    return "" if pd.isna(v) else str(v).strip()

def first_number(s):
    """First numeric token; handles commas, currency marks, ranges."""
    s = txt(s)
    if not s:
        return None
    m = re.search(r"[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[-+]?\d+(?:\.\d+)?", s)
    return float(m.group(0).replace(",", "")) if m else None

def currency_of(s):
    s = txt(s)
    if "A$" in s or "AUD" in s: return "AUD"
    if "US$" in s or "USD" in s or re.search(r"\$\d", s): return "USD"
    if "¥" in s or "JPY" in s or re.search(r"\byen\b", s, re.I): return "JPY"
    return ""

DATE_RE = re.compile(r"(\d{4})[/\-](\d{1,2})(?:[/\-](\d{1,2}))?|(?<!\d)(\d{4})(?!\d)")
def parse_date(s):
    """-> (iso_string, precision) with precision in {day, month, year, ''}."""
    s = txt(s)
    if not s or s.upper().startswith("TBV"):
        return "", ""
    m = DATE_RE.search(s)
    if not m:
        return "", ""
    if m.group(1):
        y, mo, d = m.group(1), int(m.group(2)), m.group(3)
        if d:
            return f"{y}-{mo:02d}-{int(d):02d}", "day"
        return f"{y}-{mo:02d}", "month"
    return m.group(4), "year"

def label_encode(series, field, codebook, zero_label="(blank)"):
    labels = sorted({v for v in series if v})
    mapping = {v: i + 1 for i, v in enumerate(labels)}
    codebook.append((field, 0, zero_label))
    for v, i in mapping.items():
        codebook.append((field, i, v))
    return series.map(lambda v: mapping.get(v, 0))

# ---------------- categorical groupers (order matters; first match wins) ----
def category_group(raw):
    r = raw.lower()
    if "activist" in r or "campaign" in r: return "Activist campaign"
    if "mbo" in r or "take-private" in r or "take private" in r or "privatization" in r or "employee buyout" in r: return "Take-private / MBO"
    if "outbound" in r or ("cross-border" in r and "inbound" not in r): return "Cross-border outbound"
    if "parent" in r or "carve-out" in r or "carve out" in r or "subsidiary" in r or "buy-in" in r: return "Parent-subsidiary / carve-out"
    if "hostile" in r or "contested" in r or "consentless" in r or "unsolicited" in r or "counter" in r or "bidding war" in r or "interloper" in r or "blocked" in r or "white-knight" in r or "white knight" in r: return "Contested / hostile bid"
    if "tob" in r or "tender" in r or "merger" in r or "acquisition" in r or "recapitalization" in r: return "Strategic TOB"
    return "Other" if r else ""

INDUSTRY_MAP = [
    (r"bank|insur|financial|asset manage|leasing|securit|life\b", "Financials"),
    (r"semiconductor|chip|electron|photoresist|substrate|timing|thermistor|solder", "Semiconductors / electronics"),
    (r"machin|industrial|construction|robot|elevator|glass|steel|paint|chemical|composite|materials|aviation|aircraft", "Industrials / machinery"),
    (r"retail|consumer|convenience|department|drugstore|supermarket|cosmetic|food|restaurant|outdoor|apparel|fried", "Retail / consumer"),
    (r"energy|gas|oil|refin|power\b", "Energy"),
    (r"pharma|health|medical|drug\b|nursing", "Healthcare / pharma"),
    (r"hr\b|staffing|outsourc|benefit|services", "HR / staffing / services"),
    (r"software|internet|it |information|digital|media|telecom|comics|data|computer|price comparison", "Technology / software"),
    (r"auto|mobility|motor|clutch|vehicle", "Automotive / mobility"),
    (r"print|packag", "Printing / materials"),
]
def industry_group(raw):
    r = raw.lower()
    if not r: return ""
    for pat, lab in INDUSTRY_MAP:
        if re.search(pat, r): return lab
    return "Other"

def outcome_code(raw):
    r = raw.lower()
    if not r: return ""
    if re.search(r"fail|withdraw|withdrew|blocked|terminat|cancel", r): return "Failed"
    if re.search(r"conclud|complet|delist|squeeze-out (completed|effective)", r): return "Concluded"
    return "Other/Unclear"

def exchange_of(raw):
    r = raw
    for lab in ["TSE Prime", "TSE Standard", "TSE Growth", "NYSE", "Nasdaq", "ASX", "Euronext"]:
        if lab.lower() in r.lower(): return lab
    if "unlisted" in r.lower() or "private" in r.lower(): return "Unlisted"
    if "tse" in r.lower(): return "TSE (segment unspecified)"
    return "Other" if r else ""

def board_code(raw):
    r = raw.lower()
    if not r: return ""
    if "tbv" in r and len(r) < 30: return "Unclear/TBV"
    opposed = "oppos" in r
    forr = re.search(r"support|favor|favour|recommend|unanimous", r)
    neutral = "neutral" in r or "withdrew" in r or "withdrawn" in r or "reserv" in r or "switched" in r or "mixed" in r
    if neutral and (forr or opposed): return "Mixed"
    if neutral: return "Mixed"
    if opposed and forr: return "Mixed"
    if opposed: return "Opposed"
    if forr: return "For"
    if "engag" in r: return "Engaged"
    if "no formal" in r or "none" in r: return "No formal recommendation"
    return "Other"

def yn_flag(raw, yes_pat, no_pat):
    r = raw.lower()
    if not r: return ""
    if "tbv" in r and not re.search(yes_pat, r) and not re.search(no_pat, r): return "Unclear/TBV"
    if re.search(no_pat, r): return "No"
    if re.search(yes_pat, r): return "Yes"
    return "Other"

def squeeze_code(raw):
    r = raw.lower()
    if not r or r.startswith("n/a"): return ""
    if "consolidation" in r or "reverse" in r: return "Share consolidation"
    if "share exchange" in r: return "Share exchange"
    if "scheme" in r: return "Scheme of arrangement"
    if "merger" in r: return "Merger"
    if "tbv" in r or "expected" in r: return "Unclear/TBV"
    return "Unclear/TBV"

def verification_code(raw):
    r = raw.lower()
    if not r: return ""
    if "verified" in r: return "Verified (primary/current sources)"
    if "high" in r: return "High confidence"
    if "medium" in r: return "Medium - needs verification"
    if "low" in r: return "Low - needs verification"
    return "Unclear"

REG_FLAGS = {
    "has_JFTC": r"jftc|anti-?monopoly", "has_FSA": r"\bfsa\b|financial services agency",
    "has_METI": r"\bmeti\b", "has_CFIUS": r"cfius", "has_FEFTA": r"fefta|foreign exchange",
    "has_China_SAMR": r"samr|china", "has_EU_regulator": r"\beu\b|european|\bec\b|fsr|france|germany|italy",
    "has_DOJ_FTC_HSR": r"\bdoj\b|\bftc\b|\bhsr\b", "has_FIRB": r"firb|australia",
    "has_SEC": r"\bsec\b", "has_Bermuda_BMA": r"\bbma\b|bermuda", "has_Broadcast_Act": r"broadcast",
    "has_MoF": r"\bmof\b|ministry of finance",
}
RULE_FLAGS = {
    "mentions_FIEA": r"fiea|financial instruments", "mentions_METI_guidelines": r"meti|guideline",
    "mentions_Companies_Act": r"companies act", "mentions_FEFTA": r"fefta|foreign exchange",
    "mentions_CFIUS": r"cfius", "mentions_TSE_reform": r"tse",
}
ACTIVISTS = {
    "activist_Effissimo": r"effissimo", "activist_Farallon": r"farallon", "activist_Elliott": r"elliott",
    "activist_3D_Investment": r"3d invest|3d\+|3d ", "activist_King_Street": r"king street",
    "activist_ValueAct": r"valueact", "activist_Oasis": r"oasis", "activist_Murakami": r"murakami|city index",
    "activist_YFO": r"yfo|yamauchi", "activist_Dalton": r"dalton", "activist_Ancora": r"ancora",
    "activist_Artisan_Partners": r"artisan", "activist_MY_Alpha": r"my.?alpha", "activist_Palliser": r"palliser",
    "activist_Orbis": r"orbis",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="Japan_Master.csv")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--dated", action="store_true")
    a = ap.parse_args()

    m = pd.read_csv(a.master, encoding="utf-8-sig").astype(object)
    assert m["Deal ID"].is_unique, "duplicate Deal IDs"
    o = pd.DataFrame()
    codebook = []

    o["deal_id"] = m["Deal ID"].map(txt)
    o["category_raw"] = m["Category"].map(txt)
    o["category_group"] = o["category_raw"].map(category_group)
    o["category_code"] = label_encode(o["category_raw"], "category_code", codebook)
    o["category_group_code"] = label_encode(o["category_group"], "category_group_code", codebook)

    ann = m["Date Announced"].map(txt)
    d = ann.map(parse_date)
    o["date_announced"], o["date_announced_precision"] = d.map(lambda t: t[0]), d.map(lambda t: t[1])
    o["date_announced_year"] = o["date_announced"].str[:4]
    comp = m["Date Completed / Failed"].map(txt)
    d = comp.map(parse_date)
    o["date_completed_or_failed"], o["date_completed_precision"] = d.map(lambda t: t[0]), d.map(lambda t: t[1])
    o["time_to_close_months"] = m["Time to Close (months)"].map(lambda v: first_number(v))
    o["conclusion_status_raw"] = m["Conclusion / Status"].map(txt)
    o["outcome_code"] = o["conclusion_status_raw"].map(outcome_code)
    o["outcome_code_num"] = label_encode(o["outcome_code"], "outcome_code_num", codebook)

    o["target_full_name"] = m["Target Full Name"].map(txt)
    o["target_ticker_exchange_raw"] = m["Target Ticker / Exchange"].map(txt)
    o["target_ticker_code"] = o["target_ticker_exchange_raw"].map(
        lambda s: (re.search(r"\b(\d{4})\b", s) or [None]) and (re.search(r"\b(\d{4})\b", s).group(1) if re.search(r"\b(\d{4})\b", s) else ""))
    o["target_exchange"] = o["target_ticker_exchange_raw"].map(exchange_of)
    o["target_exchange_code"] = label_encode(o["target_exchange"], "target_exchange_code", codebook)
    o["industry_raw"] = m["Industry"].map(txt)
    o["industry_group"] = o["industry_raw"].map(industry_group)
    o["industry_group_code"] = label_encode(o["industry_group"], "industry_group_code", codebook)
    o["acquirer_full_name"] = m["Acquirer Full Name"].map(txt)
    o["acquirer_exchange_raw"] = m["Acquirer Listed Exchange"].map(txt)
    o["acquirer_is_unlisted"] = o["acquirer_exchange_raw"].str.contains("unlisted", case=False)

    usd = m["Deal Size (US$ mn)"].map(txt)
    o["deal_size_usd_mn"] = usd.map(first_number)
    o["deal_size_usd_is_estimate"] = usd.map(is_est)
    o["deal_size_usd_is_stake_value"] = o["category_raw"].str.contains("Activist", case=False)
    loc = m["Deal Size (local, JPY bn unless noted)"].map(txt)
    def loc_parse(s):
        v = first_number(s)
        if v is None: return None, "", ""
        note = "bn"
        if re.search(r"\btn\b|trillion", s, re.I):
            v, note = v * 1000, "converted_tn_to_bn"
        cur = currency_of(s) or "JPY"
        return v, cur, note
    parsed = loc.map(loc_parse)
    o["deal_size_local_value_bn"] = parsed.map(lambda t: t[0])
    o["deal_size_local_currency"] = parsed.map(lambda t: t[1])
    o["deal_size_local_is_estimate"] = loc.map(is_est)
    o["deal_size_local_scale_note"] = parsed.map(lambda t: t[2])

    o["deal_structure_raw"] = m["Deal Structure"].map(txt)
    st = o["deal_structure_raw"].str.lower()
    o["structure_has_TOB"] = st.str.contains("tob|tender")
    o["structure_has_squeeze_out"] = st.str.contains("squeeze|consolidation")
    o["structure_has_MBO"] = st.str.contains("mbo")
    o["structure_has_merger"] = st.str.contains("merger")
    o["structure_has_scheme"] = st.str.contains("scheme")
    o["structure_has_share_sale"] = st.str.contains("share sale|block|allotment|carve")
    o["structure_has_proxy_contest"] = st.str.contains("proxy")

    fpx = m["Final Offer Price (local)"].map(txt)
    o["final_offer_price_value"] = fpx.map(first_number)
    o["final_offer_price_currency"] = fpx.map(currency_of)
    o["final_offer_price_is_estimate"] = fpx.map(is_est)
    o["final_offer_price_raw"] = fpx
    bumps = m["Initial Offer / Price Bumps"].map(txt)
    o["initial_offer_price_value"] = bumps.map(first_number)
    o["initial_offer_price_currency"] = bumps.map(currency_of)
    def bump_count(s):
        mm = re.search(r"(\d+)\s*bumps?\b", s)
        if mm: return int(mm.group(1))
        n = s.count("→")
        return n if n else (0 if re.search(r"no bump", s, re.I) else None)
    o["price_bump_count"] = bumps.map(lambda s: bump_count(s) if s else None)
    def was_bumped(s, n):
        if not s: return ""
        if n is None: return "Unclear/TBV" if "TBV" in s else ""
        return "True" if n and n > 0 else "False"
    o["price_was_bumped"] = [was_bumped(s, n) for s, n in zip(bumps, o["price_bump_count"])]
    o["initial_offer_price_bumps_raw"] = bumps

    upx = m["Unaffected Price (local)"].map(txt)
    o["unaffected_price_value"] = upx.map(first_number)
    o["unaffected_price_currency"] = upx.map(currency_of)
    o["unaffected_price_is_estimate"] = upx.map(is_est)
    o["unaffected_price_raw"] = upx
    prem = m["Premium to Unaffected (%)"].map(txt)
    o["premium_pct_value"] = prem.map(lambda s: first_number(s) if s and not s.upper().startswith("TBV") else None)
    o["premium_pct_is_estimate"] = prem.map(is_est)
    o["premium_pct_raw"] = prem

    brd = m["Board Recommendation"].map(txt)
    o["board_recommendation_raw"] = brd
    o["board_recommendation_code"] = brd.map(board_code)
    o["board_recommendation_code_num"] = label_encode(o["board_recommendation_code"], "board_recommendation_code_num", codebook)
    spc = m["Special Committee"].map(txt)
    o["special_committee_raw"] = spc
    o["special_committee_flag"] = spc.map(lambda s: yn_flag(s, r"yes|committee|established|formed|written report", r"^no\b|none"))
    cb = m["Competing Bid / Interloper"].map(txt)
    o["competing_bid_raw"] = cb
    o["competing_bid_flag"] = cb.map(lambda s: yn_flag(s, r"yes|counter|rival|interloper|competing|auction|bidding", r"^no\b|none"))
    rec = m["Recurring Attempt by Same Acquirer?"].map(txt)
    o["recurring_acquirer_raw"] = rec
    o["recurring_acquirer_flag"] = rec.map(lambda s: yn_flag(s, r"yes|prior|serial|second|again|before", r"^no\b|none|first"))

    toe = m["Toehold / Irrevocables / Tender Agreements"].map(txt)
    o["toehold_raw"] = toe
    o["toehold_present_flag"] = toe.map(lambda s: bool(s) and not re.match(r"^(no toehold|none)\b", s, re.I))
    o["toehold_pct_value"] = toe.map(lambda s: first_number(re.search(r"[\d.]+\s*%", s).group(0)) if re.search(r"[\d.]+\s*%", s) else None)
    o["toehold_is_estimate"] = toe.map(is_est)

    regs = [m[f"Regulator {i}"].map(txt) for i in (1, 2, 3)]
    for i, r in enumerate(regs, 1):
        o[f"regulator_{i}_raw"] = r
    o["num_regulators"] = sum(r.map(lambda s: 1 if s and s not in {"—", "-", "n/a", "N/A"} else 0) for r in regs)
    allreg = (regs[0] + " | " + regs[1] + " | " + regs[2]).str.lower()
    for col, pat in REG_FLAGS.items():
        o[col] = allreg.str.contains(pat, regex=True)
    o["has_other_foreign_antitrust_or_FDI"] = allreg.str.contains(r"foreign antitrust|merger control|fdi screening|multi-jurisdiction|vietnam|india|saudi|korea|insurance regulat")

    rules = m["Rules / Regulations Triggering Review"].map(txt)
    o["rules_regulations_triggering_review_raw"] = rules
    rl = rules.str.lower()
    for col, pat in RULE_FLAGS.items():
        o[col] = rl.str.contains(pat, regex=True)

    o["key_debate_points_raw"] = m["Key Debate Points / Frictions"].map(txt)
    act = m["Activism & Hedge Fund Involvement"].map(txt)
    o["activism_involvement_raw"] = act
    o["has_activist_involvement"] = act.map(lambda s: bool(s) and not re.match(r"^(none|tbv|n/a|no\b)", s.strip(), re.I))
    al = act.str.lower()
    for col, pat in ACTIVISTS.items():
        o[col] = al.str.contains(pat, regex=True)

    res = m["Final Resolution Mechanism"].map(txt)
    o["final_resolution_mechanism_raw"] = res
    rlow = res.str.lower()
    o["resolution_delisted_flag"] = rlow.str.contains("delist")
    o["resolution_squeeze_out_flag"] = rlow.str.contains("squeeze|consolidation")
    o["resolution_withdrawn_flag"] = rlow.str.contains("withdraw|withdrew|terminat")
    sq = m["Squeeze-out Mechanism"].map(txt)
    o["squeeze_out_mechanism_raw"] = sq
    o["squeeze_out_mechanism_code"] = sq.map(squeeze_code)
    o["squeeze_out_mechanism_code_num"] = label_encode(o["squeeze_out_mechanism_code"], "squeeze_out_mechanism_code_num", codebook)

    dl = m["Delisting Date"].map(txt)
    o["delisting_date_raw"] = dl
    dd = dl.map(parse_date)
    o["delisting_date"], o["delisting_date_precision"] = dd.map(lambda t: t[0]), dd.map(lambda t: t[1])
    o["delisting_date_is_estimate"] = dl.map(is_est)

    ver = m["Verification Status"].map(txt)
    o["verification_status_raw"] = ver
    o["verification_confidence_code"] = ver.map(verification_code)
    o["verification_confidence_code_num"] = label_encode(o["verification_confidence_code"], "verification_confidence_code_num", codebook)
    o["verification_has_open_followups"] = ver.str.contains(r"TBV|follow|confirm|monitor|approximate|needs", case=False)
    o["notes_raw"] = m["Notes / Follow-ups"].map(txt)

    # ---- Phase 1b columns (v3): passthrough + parsed numerics ------------
    P1B = {
        "Filing / First Report Date": "filing_first_report_date_raw",
        "Pre-Event Close (T-1, local)": "pre_event_close_raw",
        "Post-Event Close (T+1, local)": "post_event_close_raw",
        "Premium to T-1 Close (%)": "premium_t1_pct_raw",
        "Market Reaction T+1 (%)": "reaction_t1_pct_raw",
        "Min Tender Condition (Y/N)": "min_tender_condition_flag",
        "Min Tender Condition Detail": "min_tender_condition_detail_raw",
        "Fairness Opinion Provider": "fairness_opinion_provider_raw",
        "Financial Advisor (Target)": "fa_target_raw",
        "Financial Advisor (Acquirer)": "fa_acquirer_raw",
        "Target IPO Lead Underwriter": "target_ipo_underwriter_raw",
        "FEFTA Classification": "fefta_classification_raw",
        "Financing Description": "financing_description_raw",
        "Break Fee (Y/N)": "break_fee_flag",
        "Break Fee Amount": "break_fee_amount_raw",
        "TSE Segment": "tse_segment",
        "Index Membership": "index_membership_raw",
        "Founder/Family Ownership %": "founder_family_ownership_raw",
        "Key Management Age at Announcement": "key_management_age_raw",
        "PBR at Announcement": "pbr_at_announcement_raw",
    }
    for src, dst in P1B.items():
        if src in m.columns:
            o[dst] = m[src].map(txt)
    for src, dst in [("Pre-Event Close (T-1, local)", "pre_event_close_value"),
                     ("Post-Event Close (T+1, local)", "post_event_close_value"),
                     ("Premium to T-1 Close (%)", "premium_t1_pct_value"),
                     ("Founder/Family Ownership %", "founder_family_ownership_pct"),
                     ("PBR at Announcement", "pbr_at_announcement_value")]:
        if src in m.columns:
            o[dst] = m[src].map(lambda s: first_number(s) if txt(s) and not txt(s).upper().startswith("TBV") else None)

    for i, col in enumerate(["Source URL 1 (primary)", "Source URL 2", "Source URL 3"], 1):
        raw = m[col].map(txt)
        o[f"source_url_{i}"] = raw.map(lambda s: (re.search(r"https?://\S+", s).group(0).rstrip(")") if re.search(r"https?://\S+", s) else ""))
    o["is_fully_cited"] = o["source_url_1"].str.startswith("http")

    # ---- integrity gates -------------------------------------------------
    assert len(o) == len(m)
    assert o["deal_id"].is_unique
    assert o["date_announced"].ne("").all(), "missing announce dates"
    assert o["is_fully_cited"].all(), "citation gate failed: uncited row present"

    out_csv = f"{a.outdir}/Japan.csv"
    o.to_csv(out_csv, index=False, encoding="utf-8-sig")
    with open(f"{a.outdir}/Japan_Codebook.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["field", "code", "label"]); w.writerows(codebook)
    if a.dated:
        o.to_csv(f"{a.outdir}/Japan_{datetime.date.today().isoformat()}.csv", index=False, encoding="utf-8-sig")
    print(f"OK: {len(o)} rows x {len(o.columns)} cols -> {out_csv}; codebook {len(codebook)} entries")
    return 0

if __name__ == "__main__":
    sys.exit(main())
