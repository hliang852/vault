"""
precedent_engine.py

Turns Japan.csv into a precedent-linking dataset for the case-law-style
playbook viewer: a similarity score between every pair of the 62 deals,
a trimmed nearest-neighbor graph (so the chart stays readable), and a
short human-readable "brief" per case.

This is deliberately NOT a predictive model. It is a transparent,
rule-based analogy engine: two deals are "close" because they share
specific, nameable facts (same category family, same regulator, same
named activist, same board posture, etc). Every edge can be explained
in one sentence -- that explainability is the point, since the use
case is "find me the comparable precedent," not "predict the outcome."
"""
import pandas as pd
import numpy as np
import json
import re
import sys
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import k_clique_communities

sys.path.insert(0, str(Path(__file__).resolve().parent))
from axes import compute_axes  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = REPO_ROOT / 'data' / 'Japan.csv'
OUTPUT_JSON = REPO_ROOT / 'output' / 'precedent_graph_data.json'

df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')

# ---------------------------------------------------------------
# 1. Feature definition -- each feature has a WEIGHT (how strong a
#    signal a match on this feature is for "these are comparable
#    precedents") and a way to read the value off the row.
#    Weights are a judgment call, not a fitted parameter -- tune
#    these based on what YOU think matters most as a practitioner.
# ---------------------------------------------------------------

CATEGORICAL_FEATURES = {
    'category_group': 2.0,      # same deal archetype = strong signal
    'industry_group': 1.0,
    'board_recommendation_code': 0.75,
    'competing_bid_flag': 1.0,
    'special_committee_flag': 0.5,
    'recurring_acquirer_flag': 0.5,
    'outcome_code': 0.5,
    'squeeze_out_mechanism_code': 0.5,
}

BOOLEAN_FEATURES = {
    'structure_has_TOB': 0.5,
    'structure_has_MBO': 1.5,          # MBO mechanics are quite distinct
    'structure_has_squeeze_out': 0.25,
    'structure_has_merger': 1.0,
    'structure_has_scheme': 1.5,       # rare structure -> strong signal when shared
    'has_activist_involvement': 0.75,
    'acquirer_is_unlisted': 0.5,
    'has_JFTC': 0.1,                   # near-universal, weak signal
    'has_CFIUS': 2.0,                  # rare, very strong signal when shared
    'has_METI': 1.5,
    'has_FEFTA': 1.5,
    'has_China_SAMR': 1.5,
    'has_EU_regulator': 1.5,
    'has_DOJ_FTC_HSR': 1.0,
    'has_FIRB': 1.5,

    # -- added this session (2026-07-06), weights grounded in real rarity
    #    numbers pulled from Japan.csv (see docs/Architecture.md) --
    'price_was_bumped_bool': 1.0,       # true in 7/62 -- rare, meaningfully distinct price-discovery signal
    'multi_jurisdiction': 0.5,          # num_regulators>=2 true in 29/62 -- moderately common
    'toehold_present_flag': 0.25,       # pre-existing column, true in 44/62 -- common, so a light weight
    'notes_flags_precedent_setting': 0.5,  # true in 7/62 -- rare but a soft/subjective text flag, kept modest
    'timeline_post_meti_2023_guideline': 0.1,  # true in 53/62 -- near-universal, weak signal like has_JFTC
    'timeline_post_tse_reform_2023': 0.1,      # true in 57/62 -- near-universal, weak signal
    'timeline_post_fiea_2026_amendment': 0.1,  # true in 0/62 today (amendment effective 2026-05-01,
    # after this corpus's cutoff) -- contributes nothing yet, will start mattering once the corpus
    # includes deals announced after that date.
}

# NOTE: instigator_type / lockup_signal_count / activist_signature (see axes.py)
# are deliberately NOT added here as scored features. Each is a pure
# recombination of columns already scored independently above (category_group,
# has_activist_involvement, acquirer_is_unlisted, toehold_present_flag,
# special_committee_flag, recurring_acquirer_flag, the activist_* match
# mechanism) -- scoring the composite too would double/triple-count the same
# underlying fact. They're exposed on each node as descriptive `axes` only.

NAMED_ACTIVIST_COLS = [c for c in df.columns if c.startswith('activist_')]
ACTIVIST_MATCH_WEIGHT = 2.5  # same specific fund named = very strong precedent link

def blank(v):
    if pd.isna(v):
        return True
    if isinstance(v, str) and v.strip() in ('', 'nan', 'Unclear/TBV', 'Other'):
        return True
    return False

def pair_score(i, j):
    """Weighted-match score between row i and row j. Returns (score, reasons[])."""
    a, b = df.loc[i], df.loc[j]
    score = 0.0
    reasons = []

    for col, w in CATEGORICAL_FEATURES.items():
        va, vb = a[col], b[col]
        if not blank(va) and not blank(vb) and va == vb:
            score += w
            reasons.append((w, f"Both: {col.replace('_', ' ')} = {va}"))

    for col, w in BOOLEAN_FEATURES.items():
        if bool(a[col]) and bool(b[col]):
            score += w
            reasons.append((w, f"Both: {col.replace('has_', '').replace('structure_', '').replace('_', ' ')}"))

    shared_funds = []
    for col in NAMED_ACTIVIST_COLS:
        if bool(a[col]) and bool(b[col]):
            fund = col.replace('activist_', '').replace('_', ' ')
            shared_funds.append(fund)
            score += ACTIVIST_MATCH_WEIGHT
            reasons.append((ACTIVIST_MATCH_WEIGHT, f"Both name activist: {fund}"))

    reasons.sort(key=lambda x: -x[0])
    return score, [r[1] for r in reasons[:4]]

# ---------------------------------------------------------------
# 2. Build full pairwise score matrix, then keep only each node's
#    top-K neighbors so the rendered graph is legible (a complete
#    graph on 62 nodes is a hairball, not an insight).
# ---------------------------------------------------------------
n = len(df)
TOP_K = 4
MIN_SCORE = 1.5  # don't force an edge if there's genuinely little in common

edges = []
neighbor_lists = {}
for i in range(n):
    scored = []
    for j in range(n):
        if i == j:
            continue
        s, reasons = pair_score(i, j)
        if s >= MIN_SCORE:
            scored.append((s, j, reasons))
    scored.sort(key=lambda x: -x[0])
    top = scored[:TOP_K]
    neighbor_lists[df.loc[i, 'deal_id']] = [
        {'id': df.loc[j, 'deal_id'], 'score': round(s, 2), 'reasons': reasons}
        for s, j, reasons in top
    ]
    for s, j, reasons in top:
        pair = tuple(sorted((i, j)))
        edges.append((pair, s, reasons))

# de-duplicate symmetric edges, keep the max score / reasons found either direction
edge_map = {}
for pair, s, reasons in edges:
    if pair not in edge_map or s > edge_map[pair][0]:
        edge_map[pair] = (s, reasons)

edge_list = [
    {'source': df.loc[i, 'deal_id'], 'target': df.loc[j, 'deal_id'],
     'score': round(s, 2), 'reasons': reasons}
    for (i, j), (s, reasons) in edge_map.items()
]

# ---------------------------------------------------------------
# 2b. Overlapping community detection (secondary/diagnostic cross-check
#     on the axis-tag clustering above, NOT the primary cluster definition
#     -- see docs/Architecture.md). Built on a full, untrimmed pairwise
#     graph at the same MIN_SCORE threshold as the viewer graph, reusing
#     pair_score() so the notion of "similar" stays identical everywhere.
# ---------------------------------------------------------------
G = nx.Graph()
G.add_nodes_from(df['deal_id'])
for i in range(n):
    for j in range(i + 1, n):
        s, _ = pair_score(i, j)
        if s >= MIN_SCORE:
            G.add_edge(df.loc[i, 'deal_id'], df.loc[j, 'deal_id'], weight=s)

K_CLIQUE = 3
communities = [sorted(c) for c in k_clique_communities(G, K_CLIQUE)]
communities.sort(key=lambda c: (-len(c), c[0]))

print(f"k-clique communities (k={K_CLIQUE}, MIN_SCORE={MIN_SCORE}): {len(communities)} found")
if communities:
    print("sizes:", [len(c) for c in communities])
    largest_frac = len(communities[0]) / n
    if largest_frac >= 0.8:
        print(f"WARNING: largest community covers {largest_frac:.0%} of all nodes -- likely degenerate, "
              f"consider raising K_CLIQUE or MIN_SCORE.")
else:
    print("WARNING: zero communities found -- K_CLIQUE or MIN_SCORE may need adjustment.")

community_ids_by_deal = {deal_id: [] for deal_id in df['deal_id']}
for idx, members in enumerate(communities):
    for deal_id in members:
        community_ids_by_deal[deal_id].append(idx)

# ---------------------------------------------------------------
# 2c. short_name: a compact display label for the viewer's node
#     labels (full target_full_name is too long/cluttered under a
#     force-graph circle). Mechanical string cleanup only -- no
#     new facts, just a shortened rendering of the existing name.
# ---------------------------------------------------------------
CORPORATE_SUFFIXES = [
    'incorporated', 'corporation', 'holdings', 'limited', 'company',
    'corp.', 'corp', 'co.', 'co', 'ltd.', 'ltd', 'inc.', 'inc', 'group',
]

def make_short_name(full_name: str) -> str:
    if not isinstance(full_name, str) or not full_name.strip():
        return full_name
    name = re.sub(r'\([^)]*\)', '', full_name)  # strip parentheticals
    name = name.strip()

    changed = True
    while changed:
        changed = False
        for suffix in CORPORATE_SUFFIXES:
            pattern = re.compile(r'[,\s]+' + re.escape(suffix) + r'\s*$', re.IGNORECASE)
            new_name = pattern.sub('', name)
            if new_name != name:
                name = new_name.strip()
                changed = True

    name = name.strip(' ,.-')
    if not name:
        name = ' '.join(full_name.split()[:3])
    return name

# ---------------------------------------------------------------
# 3. Human-readable one-paragraph brief per case, built only from
#    fields already in Japan.csv (no new facts).
# ---------------------------------------------------------------
def money_str(row):
    if not pd.isna(row['deal_size_usd_mn']):
        tag = ' (est.)' if row['deal_size_usd_is_estimate'] else ''
        stake = ' [stake value]' if row['deal_size_usd_is_stake_value'] else ''
        return f"US${row['deal_size_usd_mn']:,.0f}mn{tag}{stake}"
    return "size TBV"

def brief(row):
    parts = []
    parts.append(f"{row['acquirer_full_name']} \u2192 {row['target_full_name']}")
    parts.append(f"{row['category_raw']} | {row['industry_raw']}")
    parts.append(f"Announced {row['date_announced'] or '?'}; {money_str(row)}")
    if not blank(row['final_resolution_mechanism_raw']):
        parts.append(f"Resolution: {row['final_resolution_mechanism_raw']}")
    if not blank(row['notes_raw']):
        parts.append(f"Why it matters: {row['notes_raw']}")
    return parts

print("\nshort_name before/after (all 62 rows):")
print(f"{'deal_id':<8} {'target_full_name':<55} {'short_name'}")
for i, row in df.iterrows():
    sn = make_short_name(row['target_full_name'])
    print(f"{row['deal_id']:<8} {row['target_full_name']:<55} {sn}")

nodes = []
for i, row in df.iterrows():
    active_funds = [c.replace('activist_', '').replace('_', ' ')
                    for c in NAMED_ACTIVIST_COLS if bool(row[c])]
    features = {col: (None if blank(row[col]) else str(row[col])) for col in CATEGORICAL_FEATURES}
    features.update({col: bool(row[col]) for col in BOOLEAN_FEATURES})
    features['activist_funds'] = active_funds
    nodes.append({
        'id': row['deal_id'],
        'name': row['target_full_name'],
        'short_name': make_short_name(row['target_full_name']),
        'acquirer': row['acquirer_full_name'],
        'category_group': row['category_group'],
        'industry_group': row['industry_group'],
        'outcome': row['outcome_code'] if not blank(row['outcome_code']) else 'Unclear',
        'year': str(row['date_announced_year']) if not blank(row['date_announced_year']) else '?',
        'deal_size_usd_mn': None if pd.isna(row['deal_size_usd_mn']) else float(row['deal_size_usd_mn']),
        'brief': brief(row),
        'verification': row['verification_confidence_code'],
        'features': features,
        'axes': compute_axes(row, NAMED_ACTIVIST_COLS),
        'community_ids': community_ids_by_deal[row['deal_id']],
    })

data = {
    'nodes': nodes,
    'edges': edge_list,
    'communities': communities,
    'weights': {
        'categorical': CATEGORICAL_FEATURES,
        'boolean': BOOLEAN_FEATURES,
        'activist_match': ACTIVIST_MATCH_WEIGHT,
    },
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=None)

print(f"nodes: {len(nodes)}  edges: {len(edge_list)}")
print("avg neighbors/node:", round(2 * len(edge_list) / n, 2))
print("sample edge:", edge_list[0])
