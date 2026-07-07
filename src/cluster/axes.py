"""
axes.py

Descriptive interpretive "axes" for a single Japan.csv row -- re-framings
of existing/derived columns as analytical dimensions, not new facts. Ports
the working logic from notebooks/exploratory_analysis.py's Lenses 1-6/8
into reusable functions for src/cluster/precedent_engine.py to attach to
each node (see Claude.md's product vision: axis tags are the primary,
rule-based multi-membership "cluster" signal).

Also carries a small Jaccard co-occurrence helper (ported from the
notebook's Section 4) used to empirically check the full feature set
scored by precedent_engine.py for double-counted signals.
"""
import itertools
import pandas as pd


def blank(v) -> bool:
    """Mirrors precedent_engine.py's blank(): True if unusable for a feature match."""
    if pd.isna(v):
        return True
    if isinstance(v, str) and v.strip() in ('', 'nan', 'Unclear/TBV', 'Other'):
        return True
    return False


def _price_discovery_type(row) -> str:
    bumped = bool(row.get('price_was_bumped_bool', False))
    board = row.get('board_recommendation_code')
    competing = row.get('competing_bid_flag')
    is_mbo = bool(row.get('structure_has_MBO', False))

    if is_mbo and competing == 'Yes':
        return 'MBO with interloper risk'
    if bumped and competing == 'Yes':
        return 'Bidding war (bumped + competing bid)'
    if bumped and board == 'Mixed':
        return 'Bumped, board split'
    if bumped:
        return 'Bumped, board aligned'
    if is_mbo:
        return 'MBO, single negotiated price'
    return 'Single negotiated, no bump'


def _instigator_type(row) -> str:
    if row.get('category_group') == 'Activist campaign' or bool(row.get('has_activist_involvement', False)):
        return 'Activist-instigated'
    if bool(row.get('acquirer_is_unlisted', False)) or row.get('category_group') == 'Take-private / MBO':
        return 'Sponsor-instigated'
    return 'Strategic-instigated'


def _lockup_signal_count(row) -> int:
    return (
        int(bool(row.get('toehold_present_flag', False)))
        + int(row.get('special_committee_flag') == 'Yes')
        + int(row.get('recurring_acquirer_flag') == 'Yes')
    )


def _activist_signature(row, activist_columns: list):
    funds = [c.replace('activist_', '').replace('_', ' ') for c in activist_columns if bool(row.get(c, False))]
    return ', '.join(sorted(funds)) if funds else None


def compute_axes(row, activist_columns: list) -> dict:
    """Returns the 7 descriptive axes for one Japan.csv row (a pandas Series)."""
    num_reg = row.get('num_regulators')
    notes_raw = row.get('notes_raw')

    return {
        'consent': None if blank(row.get('board_recommendation_code')) else row.get('board_recommendation_code'),
        'price_discovery_type': _price_discovery_type(row),
        'regulatory_friction': (
            None if pd.isna(num_reg) else ('Multi-jurisdiction' if num_reg >= 2 else 'Domestic/single-jurisdiction')
        ),
        'precedent_value_text': {
            'text': None if blank(notes_raw) else notes_raw,
            'flagged_precedent_setting': bool(row.get('notes_flags_precedent_setting', False)),
        },
        'instigator_type': _instigator_type(row),
        'lockup_signal_count': _lockup_signal_count(row),
        'activist_signature': _activist_signature(row, activist_columns),
    }


def jaccard(a: pd.Series, b: pd.Series) -> float:
    a, b = a.fillna(False).astype(bool), b.fillna(False).astype(bool)
    union = (a | b).sum()
    return (a & b).sum() / union if union else float('nan')


def top_cooccurring_pairs(df: pd.DataFrame, cols: list, min_support: int = 3, top_n: int = 20) -> pd.DataFrame:
    """Jaccard overlap across every pair of boolean-like columns in `cols`,
    excluding pairs where either side is true in fewer than `min_support` rows
    (co-occurrence on 1-2 rows is noise). Mirrors the notebook's Section 4.
    """
    rows = []
    for c1, c2 in itertools.combinations(cols, 2):
        n1 = df[c1].fillna(False).astype(bool).sum()
        n2 = df[c2].fillna(False).astype(bool).sum()
        if n1 < min_support or n2 < min_support:
            continue
        j = jaccard(df[c1], df[c2])
        if j > 0:
            rows.append({'feature_a': c1, 'feature_b': c2, 'jaccard': round(j, 2), 'n_a': int(n1), 'n_b': int(n2)})
    return pd.DataFrame(rows).sort_values('jaccard', ascending=False).head(top_n).reset_index(drop=True)
