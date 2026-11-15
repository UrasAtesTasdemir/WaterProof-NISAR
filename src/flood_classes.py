"""OPERA DSWx WTR code mapping for flood validation (docs/FLOOD_VALIDATION_PROTOCOL.md section 3).

Separate tables per product (never assumed equal). Sources (verbatim tables in the protocol):
- DSWx-HLS: JPL D-107395 Rev B, Table 4-1, Layer 1 (spec for product v1.0; files are v1.1, stated limitation).
- DSWx-S1:  JPL D-108761 Rev A, Table 4-1, Layer 1 (spec for DSWX-SAR v1.0; files are software 1.2).
Codes not in a product's table are UNDEFINED: excluded, never water, never not-water, always counted.
"""
import numpy as np

OPEN, NOT_WATER, PARTIAL, INVALID, UNDEFINED = 'open_water', 'not_water', 'partial_or_inundated', 'invalid', 'undefined'
VALID_FRACTION_MIN = 0.70

CODES = {
    'HLS': {0: NOT_WATER, 1: OPEN, 2: PARTIAL, 252: INVALID, 253: INVALID, 254: INVALID, 255: INVALID},
    'S1': {0: NOT_WATER, 1: OPEN, 3: PARTIAL, 250: INVALID, 251: INVALID, 255: INVALID},
}
SPEC_NAMES = {
    'HLS': {0: 'Not water', 1: 'Open water', 2: 'Partial surface water', 252: 'Snow/ice',
            253: 'Cloud/cloud shadow and adjacent to cloud/cloud shadow', 254: 'Ocean masked', 255: 'Fill value (no data)'},
    'S1': {0: 'Not water', 1: 'Open water', 3: 'Inundated vegetation', 250: 'Height Above Nearest Drainage (HAND) masked',
           251: 'Layover/shadow masked', 255: 'Fill value (no data)'},
}
ROLES = (OPEN, NOT_WATER, PARTIAL, INVALID, UNDEFINED)


def role_map(codes, product):
    """Array of role names for an array of WTR codes (UNDEFINED for codes not in this product's table)."""
    table = CODES[product]
    codes = np.asarray(codes)
    out = np.full(codes.shape, UNDEFINED, dtype=object)
    for code, role in table.items():
        out[codes == code] = role
    return out


def masks(codes, product):
    """Boolean masks per role. 'valid' = open + not water + partial (invalid and undefined excluded)."""
    roles = role_map(codes, product)
    m = {r: roles == r for r in ROLES}
    m['valid'] = m[OPEN] | m[NOT_WATER] | m[PARTIAL]
    return m


def summarize(codes, product):
    codes = np.asarray(codes)
    total = codes.size
    values, counts = np.unique(codes, return_counts=True)
    hist = {int(v): int(c) for v, c in zip(values, counts)}
    m = masks(codes, product)
    valid = int(m['valid'].sum())
    frac = lambda x: float(x) / total if total else 0.0
    return dict(pixels=total, histogram=hist,
                undefined_codes=sorted(int(v) for v in values if int(v) not in CODES[product]),
                valid_fraction=frac(valid), invalid_fraction=frac(m[INVALID].sum()), undefined_fraction=frac(m[UNDEFINED].sum()),
                open_water_share_of_valid=float(m[OPEN].sum()) / valid if valid else None,
                partial_share_of_valid=float(m[PARTIAL].sum()) / valid if valid else None,
                usable=bool(frac(valid) >= VALID_FRACTION_MIN))
