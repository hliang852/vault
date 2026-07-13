"""
build.py -- Part 3 site generator.

Assembles the self-contained precedent-atlas site (viewer/index.html) from
the artifacts Part 2 already produces -- nothing here invents facts or
re-derives similarity. Inputs:

  output/precedent_graph_data.json  (Part 2)   nodes/edges/communities/weights,
                                               each node's features + axes.
  data/Japan.csv                    (Part 1)   tickers, dates, prices, the
                                               narrative dossier fields.
  viewer/layout.json                (this dir) the hand-tuned 2-D arrangement
                                               of the Part 2 graph (positions
                                               only; regenerable, committed so
                                               the map stays visually stable).
  content/cases/<deal_id>.md        (plug-in)  executive summaries + links +
                                               testimonies, per Case_Content_Spec.
                                               Absent today -> dossiers render
                                               their designed "pending" slots.

Output: viewer/index.html (template.html with the DATA blob injected).

The live finder in the page scores a user's hypothetical deal against all 62
cases by replaying Part 2's pair_score weights in JS -- so this build embeds
each node's `features` and the `weights` table verbatim, and the browser does
the same weighted-match arithmetic precedent_engine.py does. Precedent index,
never a prediction.
"""
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GRAPH = REPO / 'output' / 'precedent_graph_data.json'
CSV = REPO / 'japan-ma' / 'data' / 'Japan.csv'   # canonical Part 1 output
LAYOUT = REPO / 'viewer' / 'layout.json'
CONTENT_DIR = REPO / 'content' / 'cases'
TEMPLATE = REPO / 'viewer' / 'template.html'
OUT = REPO / 'viewer' / 'index.html'

VIEWBOX_W, VIEWBOX_H = 1000, 640
NEIGHBOR_K = 5
VALID_SOURCES = {'filing', 'exchange', 'news', 'company', 'regulator', 'other'}


def die(msg):
    print(f"BUILD FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------- inputs
def load_inputs():
    if not GRAPH.exists():
        die(f"{GRAPH} missing -- run `python src/cluster/precedent_engine.py` first.")
    graph = json.loads(GRAPH.read_text(encoding='utf-8'))
    layout = json.loads(LAYOUT.read_text(encoding='utf-8'))
    rows = {}
    with open(CSV, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows[r['deal_id']] = r
    return graph, layout, rows


# ---------------------------------------------------------------- helpers
def blank(v):
    return v is None or (isinstance(v, str) and v.strip() in ('', 'nan', 'Unclear/TBV', 'Other'))


def truthy(v):
    return isinstance(v, str) and v.strip().lower() in ('true', '1', 'yes')


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def ticker(row):
    code = num(row.get('target_ticker_code'))
    if code is None:
        return None
    return f"{int(code)} JP Equity"


def radius(size):
    """Node radius from real deal size (sqrt scale). Matches the approved map."""
    if not size:
        return 6.0
    return round(max(6.0, 6.03 + 0.0829 * math.sqrt(size)), 1)


def money(size, est=False, stake=False):
    if not size:
        return None
    if size >= 1000:
        s = f"US${size / 1000:.1f}bn"
    else:
        s = f"US${size:,.0f}mn"
    if est:
        s += " (est.)"
    if stake:
        s += " · stake value"
    return s


def ensure_layout(layout, graph_nodes):
    """Auto-place any node missing from layout.json, then persist.

    Existing positions are never moved (the committed arrangement is the
    approved look); each new node is placed deterministically (seeded from its
    deal_id) near the centroid of its archetype's already-positioned nodes,
    then collision-relaxed against everything. Keeps the map stable as the
    Part 1 pipeline appends deals.
    """
    missing = [gn for gn in graph_nodes if gn['id'] not in layout]
    if not missing:
        return False

    groups = {}
    for gn in graph_nodes:
        if gn['id'] in layout:
            groups.setdefault(gn['category_group'], []).append(layout[gn['id']])

    def centroid(cg):
        pts = groups.get(cg)
        if not pts:
            return VIEWBOX_W / 2, VIEWBOX_H / 2
        return (sum(p['x'] for p in pts) / len(pts),
                sum(p['y'] for p in pts) / len(pts))

    # working set: id -> [x, y, r, movable]
    rad = {gn['id']: radius(gn.get('deal_size_usd_mn')) for gn in graph_nodes}
    pts = {did: [p['x'], p['y'], rad.get(did, 8.0), False] for did, p in layout.items()}
    for gn in sorted(missing, key=lambda g: g['id']):
        cx, cy = centroid(gn['category_group'])
        h = int(hashlib.md5(gn['id'].encode()).hexdigest(), 16)
        ang = (h % 3600) / 3600 * 2 * math.pi
        dist = 40 + (h // 3600) % 90
        pts[gn['id']] = [cx + math.cos(ang) * dist, cy + math.sin(ang) * dist,
                         rad.get(gn['id'], 8.0), True]

    ids = sorted(pts)
    PAD, M = 10.0, 30.0
    for _ in range(300):
        moved = False
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                pa, pb = pts[a], pts[b]
                if not (pa[3] or pb[3]):
                    continue
                dx, dy = pb[0] - pa[0], pb[1] - pa[1]
                d = math.hypot(dx, dy) or 0.01
                overlap = pa[2] + pb[2] + PAD - d
                if overlap <= 0:
                    continue
                ux, uy = dx / d, dy / d
                # anchored nodes never move; split the push among movables
                if pa[3] and pb[3]:
                    sa = sb = overlap / 2
                elif pa[3]:
                    sa, sb = overlap, 0
                else:
                    sa, sb = 0, overlap
                pa[0] -= ux * sa; pa[1] -= uy * sa
                pb[0] += ux * sb; pb[1] += uy * sb
                moved = True
        for did in ids:
            p = pts[did]
            if p[3]:
                p[0] = min(VIEWBOX_W - M, max(M, p[0]))
                p[1] = min(VIEWBOX_H - M, max(M, p[1]))
        if not moved:
            break

    for gn in missing:
        p = pts[gn['id']]
        layout[gn['id']] = {'x': round(p[0], 1), 'y': round(p[1], 1)}
    LAYOUT.write_text(json.dumps(dict(sorted(layout.items())),
                                 ensure_ascii=False, indent=0), encoding='utf-8')
    print(f"layout: auto-placed {len(missing)} new node(s), persisted to {LAYOUT.name}")
    return True


def facts(row, size):
    """Mechanical, estimate-hedged key facts for the dossier -- Japan.csv only."""
    def hedge(val_col, est_col, fmt=lambda x: x):
        v = row.get(val_col)
        if blank(v):
            return None
        out = fmt(v)
        if truthy(row.get(est_col, '')):
            out += " (est.)"
        return out

    ttc = num(row.get('time_to_close_months'))
    price = None
    if not blank(row.get('final_offer_price_value')):
        cur = row.get('final_offer_price_currency') or ''
        price = f"{cur}{row['final_offer_price_value']}".strip()
        if truthy(row.get('final_offer_price_is_estimate', '')):
            price += " (est.)"
    return {
        'size': money(size, truthy(row.get('deal_size_usd_is_estimate', '')),
                      truthy(row.get('deal_size_usd_is_stake_value', ''))),
        'announced': None if blank(row.get('date_announced')) else row['date_announced'],
        'closed': None if blank(row.get('date_completed_or_failed')) else row['date_completed_or_failed'],
        'time_to_close': None if ttc is None else f"{ttc:.1f} months",
        'offer_price': price,
        'premium': hedge('premium_pct_value', 'premium_pct_is_estimate', lambda x: f"{x}%"),
        'board': None if blank(row.get('board_recommendation_raw')) else row['board_recommendation_raw'],
        'resolution': None if blank(row.get('final_resolution_mechanism_raw')) else row['final_resolution_mechanism_raw'],
        'debate': None if blank(row.get('key_debate_points_raw')) else row['key_debate_points_raw'],
        'verification': row.get('verification_confidence_code') or None,
    }


# ---------------------------------------------------------------- content plug-in
MD_LINK = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
MD_BOLD = re.compile(r'\*\*([^*]+)\*\*')


def md_to_html(body):
    """Minimal Markdown -> HTML: ## headers, paragraphs, bold, links. No deps."""
    html, para = [], []

    def flush():
        if para:
            text = ' '.join(para)
            text = MD_BOLD.sub(r'<strong>\1</strong>', text)
            text = MD_LINK.sub(r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
            html.append(f"<p>{text}</p>")
            para.clear()

    for line in body.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith('## '):
            flush()
            html.append(f"<h3>{s[3:].strip()}</h3>")
        else:
            para.append(s)
    flush()
    return '\n'.join(html)


def load_content(deal_ids):
    """Load content/cases/<deal_id>.md per Case_Content_Spec. Fail loud on errors."""
    files = [p for p in CONTENT_DIR.glob('*.md') if p.stem != 'README']
    if not files:
        return {}
    try:
        import yaml  # noqa
    except ImportError:
        die("content/cases/*.md present but PyYAML not installed (pip install pyyaml).")
    out = {}
    for p in files:
        raw = p.read_text(encoding='utf-8')
        m = re.match(r'^---\n(.*?)\n---\n?(.*)$', raw, re.DOTALL)
        if not m:
            die(f"{p.name}: missing YAML frontmatter.")
        meta = yaml.safe_load(m.group(1)) or {}
        did = meta.get('deal_id')
        if did != p.stem:
            die(f"{p.name}: deal_id '{did}' != filename stem '{p.stem}'.")
        if did not in deal_ids:
            die(f"{p.name}: deal_id '{did}' not found in dataset.")
        if meta.get('status') not in ('draft', 'verified'):
            die(f"{p.name}: status must be 'draft' or 'verified'.")
        for link in meta.get('links') or []:
            if not str(link.get('url', '')).startswith('https://'):
                die(f"{p.name}: link url must be https:// ({link.get('url')}).")
            if link.get('source') not in VALID_SOURCES:
                die(f"{p.name}: link source '{link.get('source')}' invalid.")
        out[did] = {
            'summary_html': md_to_html(m.group(2).strip()),
            'links': meta.get('links') or [],
            'testimonies': meta.get('testimonies') or [],
            'status': meta['status'],
            'last_verified': meta.get('last_verified'),
        }
    return out


# ---------------------------------------------------------------- assemble
def build():
    graph, layout, rows = load_inputs()
    content = load_content(set(rows))
    ensure_layout(layout, graph['nodes'])

    # neighbor lists: top-K by score from the trimmed Part 2 edge set
    adj = {}
    for e in graph['edges']:
        adj.setdefault(e['source'], []).append((e['target'], e['score'], e['reasons']))
        adj.setdefault(e['target'], []).append((e['source'], e['score'], e['reasons']))

    nodes = []
    for gn in graph['nodes']:
        did = gn['id']
        row = rows.get(did)
        if row is None:
            die(f"deal_id {did} in graph but not in Japan.csv.")
        pos = layout.get(did)
        if pos is None:
            die(f"deal_id {did} missing from layout even after auto-placement -- bug in ensure_layout.")
        size = gn.get('deal_size_usd_mn')
        nbrs = sorted(adj.get(did, []), key=lambda x: -x[1])[:NEIGHBOR_K]
        nodes.append({
            'id': did,
            'sn': gn['short_name'],
            'name': gn['name'],
            'acquirer': gn['acquirer'],
            'cg': gn['category_group'],
            'industry': gn['industry_group'],
            'x': pos['x'], 'y': pos['y'], 'r': radius(size),
            'outcome': gn['outcome'], 'year': gn['year'],
            'ticker': ticker(row), 'size': size,
            'features': gn['features'],
            'axes': gn['axes'],
            'community_ids': gn['community_ids'],
            'brief': gn['brief'],
            'facts': facts(row, size),
            'neighbors': [{'id': t, 'score': s, 'reasons': r} for t, s, r in nbrs],
            'content': content.get(did),
        })

    # centroids per category_group, from the approved positions
    centroids = {}
    for nd in nodes:
        centroids.setdefault(nd['cg'], {'xs': [], 'ys': [], 'ids': []})
        centroids[nd['cg']]['xs'].append(nd['x'])
        centroids[nd['cg']]['ys'].append(nd['y'])
        centroids[nd['cg']]['ids'].append(nd['id'])
    centroids = {
        k: {'x': round(sum(v['xs']) / len(v['xs']), 1),
            'y': round(sum(v['ys']) / len(v['ys']), 1),
            'ids': v['ids'], 'count': len(v['ids'])}
        for k, v in centroids.items()
    }

    data = {
        'nodes': nodes,
        'edges': [{'s': e['source'], 't': e['target'], 'w': e['score']} for e in graph['edges']],
        'centroids': centroids,
        'weights': graph['weights'],
        'communities': graph['communities'],
        'viewbox': [VIEWBOX_W, VIEWBOX_H],
    }

    if not TEMPLATE.exists():
        die(f"{TEMPLATE} missing.")
    html = TEMPLATE.read_text(encoding='utf-8')
    if '/*__DATA__*/' not in html:
        die("template.html has no /*__DATA__*/ placeholder.")
    html = html.replace('/*__DATA__*/', json.dumps(data, ensure_ascii=False))

    # data-driven site copy: case count + coverage window from the corpus itself
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    dates = sorted(r['date_announced'] for r in rows.values() if r.get('date_announced', '').strip())
    lo, hi = dates[0], dates[-1]
    marquee = f"{lo[:4]} {months[int(lo[5:7]) - 1]} — {hi[:4]} {months[int(hi[5:7]) - 1]}"
    for token, value in [('__N_CASES__', str(len(nodes))),
                         ('__YR_SPAN__', f"{lo[:4]}–{hi[:4]}"),
                         ('__MARQUEE_SPAN__', marquee)]:
        if token not in html:
            die(f"template.html missing copy token {token}.")
        html = html.replace(token, value)
    OUT.write_text(html, encoding='utf-8')

    covered = sum(1 for n in nodes if n['content'])
    print(f"built {OUT.relative_to(REPO)}: {len(nodes)} nodes, {len(data['edges'])} edges, "
          f"{len(centroids)} clusters, {covered} dossiers with content.")


if __name__ == '__main__':
    build()
