"""'Can NISAR see my place?' — availability summaries from CACHED catalog results.

Reads only saved inventories from earlier phases (no network). Compatible pairs
are same track, frame, direction and mode (radar geometry must match for change).
"""
from collections import defaultdict
from datetime import datetime
from itertools import combinations
import json
from pathlib import Path

from rasterio.warp import transform_geom
from shapely import wkt
from shapely.geometry import shape, mapping

ROOT = Path(__file__).resolve().parents[1]
CASE_FILES = {
    'louisiana': dict(nisar='data/pair_selection/nisar_inventory.json', catalog='data/pair_selection/nisar_catalog.json',
                      aoi='data/nisar_manifest.json', references='data/pair_selection/reference_inventory.json',
                      gauge='data/validation/usgs_support_summary.json', ranking='data/pair_selection/pair_ranking.json'),
    'kerrville': dict(feasibility='data/kerrville_feasibility/feasibility.json', catalog='data/kerrville_feasibility/nisar_catalog.json',
                      references='data/kerrville_feasibility/reference_windows.json', aoi='data/kerrville_feasibility/aoi.json'),
}
USABLE_FRACTION = 0.8  # same conservative guardrail used by the saved pair-selection study


def parse_time(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00'))


def _load(path, root):
    return json.loads((Path(root) / path).read_text())


def projected_footprints(catalog, aoi_wkt, crs, root=ROOT):
    """AOI polygon and each product's catalog footprint, both in a metric UTM CRS.

    Footprints come from the cached ASF search results (``results.features``).
    Returns (aoi_polygon, {product_id: footprint_polygon}).
    """
    features = _load(catalog, root)['results']['features']
    aoi = shape(transform_geom('EPSG:4326', crs, mapping(wkt.loads(aoi_wkt))))
    prints = {f['properties']['fileID']: shape(transform_geom('EPSG:4326', crs, f['geometry'])) for f in features}
    return aoi, prints


def attach_footprints(observations, aoi, prints):
    """Store each product's footprint ∩ AOI; observations without a footprint keep None."""
    for o in observations:
        fp = prints.get(o['product_id'])
        o['footprint_in_aoi'] = None if fp is None else fp.intersection(aoi)
        o['aoi_area'] = aoi.area
    return observations


def shared_coverage(a, b):
    """Fraction of the AOI imaged on BOTH dates.

    Geometric intersection of the two catalog footprints inside the AOI when
    both are available. Otherwise falls back to min(single-date coverage), which
    is only an UPPER BOUND (two footprints can each cover part of the AOI without
    overlapping each other)."""
    if a.get('footprint_in_aoi') is not None and b.get('footprint_in_aoi') is not None:
        return a['footprint_in_aoi'].intersection(b['footprint_in_aoi']).area / a['aoi_area'], 'geometric intersection'
    return min(a['coverage'], b['coverage']), 'upper bound (min of single-date coverage; footprints unavailable)'


def compatible_pairs(observations, max_days=None):
    """All before/after pairs sharing track, frame, direction and radar mode."""
    groups = defaultdict(list)
    for o in observations:
        groups[(o['track'], o['frame'], o['direction'], o.get('mode', ''))].append(o)
    pairs = []
    for key, items in groups.items():
        items = sorted(items, key=lambda o: o['time'])
        for a, b in combinations(items, 2):
            days = (b['time'] - a['time']).total_seconds() / 86400
            if max_days is None or days <= max_days:
                coverage, method = shared_coverage(a, b)
                pairs.append(dict(track=key[0], frame=key[1], direction=key[2], before=a['time'], after=b['time'],
                                  interval_days=round(days, 2), coverage=coverage, coverage_method=method,
                                  spans_event=None,
                                  before_id=a['product_id'], after_id=b['product_id']))
    return sorted(pairs, key=lambda p: (p['before'], p['after']))


def reference_rows(records, time_key, event=None):
    rows = []
    for r in records:
        t = parse_time(r[time_key])
        cloud = r.get('tile_cloud_cover_metadata', r.get('tile_cloud_cover_percent'))
        fraction = float(r.get('valid_fraction', 0) or 0)
        counts = r.get('class_counts', r.get('aoi_class_counts', {}))
        cells = int(r.get('aoi_pixel_centers', 0))
        cloud_cells = int(counts.get('253', 0)); nodata_cells = int(counts.get('255', 0))
        if fraction >= USABLE_FRACTION:
            reason = 'usable'
        elif cloud_cells >= nodata_cells and cloud_cells:
            reason = 'mostly cloud / cloud shadow'
        elif nodata_cells:
            reason = 'mostly no data (outside swath / not observed)'
        else:
            reason = 'too few valid cells'
        rows.append(dict(product_id=r['product_id'], collection='DSWx-S1' if 'DSWx-S1' in r['product_id'] else 'DSWx-HLS',
                         time=t, valid_fraction=fraction, tile_cloud_percent=None if cloud is None else float(cloud),
                         cloud_shadow_cells=cloud_cells, no_data_cells=nodata_cells, cells=cells, reason=reason,
                         hours_from_event=None if event is None else (t - event).total_seconds() / 3600,
                         usable=fraction >= USABLE_FRACTION))
    return sorted(rows, key=lambda r: r['time'])


def louisiana(root=ROOT):
    files = CASE_FILES['louisiana']
    observations = [dict(product_id=o['product_id'], time=parse_time(o['acquisition_utc']), track=o['track'], frame=o['frame'],
                         direction=o['direction'], mode='/'.join(o['bandwidth']), polarization=o['polarization'],
                         coverage=float(o['aoi_footprint_coverage_fraction'])) for o in _load(files['nisar'], root)]
    aoi, prints = projected_footprints(files['catalog'], _load(files['aoi'], root)['aoi_wkt'], 'EPSG:32615', root)
    attach_footprints(observations, aoi, prints)
    gauge = _load(files['gauge'], root)
    event = dict(documented=False, time=None,
                 note=f"No documented flood event in the cached records for this AOI; {gauge['station']} returned "
                      f"'{gauge['status']}' for {gauge['query']['startDT']}…{gauge['query']['endDT']}.",
                 note_key='vis.note.louisiana', note_values=dict(station=gauge['station'], status=gauge['status'],
                                                                start=gauge['query']['startDT'], end=gauge['query']['endDT']))
    return mark_event_span(dict(key='louisiana', name='Louisiana (USA)', observations=sorted(observations, key=lambda o: o['time']),
                pairs=compatible_pairs(observations), consecutive=compatible_pairs(observations, max_days=12.5),
                references=reference_rows(_load(files['references'], root), 'reference_utc'), event=event,
                decision=_load(files['ranking'], root)['decision'],
                sources=list(files.values())))


def kerrville(root=ROOT):
    files = CASE_FILES['kerrville']
    k = _load(files['feasibility'], root)
    peak = parse_time(k['gauge_timing']['peak']['dateTime'])
    observations = [dict(product_id=o['product_id'], time=parse_time(o['start_utc']), track=o['track'], frame=o['frame'],
                         direction=o['direction'], mode='/'.join(o['bandwidth']), polarization=o['polarization_A'],
                         coverage=float(o['aoi_footprint_coverage_fraction']),
                         hours_from_event=(parse_time(o['start_utc']) - peak).total_seconds() / 3600)
                    for o in k['nisar_observations']]
    aoi, prints = projected_footprints(files['catalog'], _load(files['aoi'], root)['aoi_wkt'], 'EPSG:32614', root)
    attach_footprints(observations, aoi, prints)
    event = dict(documented=True, time=peak,
                 note=f"Provisional gauge peak {k['gauge_timing']['peak']['value']} ft at {k['gauge_timing']['station']} "
                      f"({k['gauge_timing']['peak']['dateTime']}). {k['gauge_timing']['warning']}",
                 note_key='vis.note.kerrville', note_values=dict(value=k['gauge_timing']['peak']['value'], station=k['gauge_timing']['station'],
                                                                time=k['gauge_timing']['peak']['dateTime'], warning=k['gauge_timing']['warning']))
    return mark_event_span(dict(key='kerrville', name='Kerrville, Texas (USA)', observations=sorted(observations, key=lambda o: o['time']),
                pairs=compatible_pairs(observations), consecutive=compatible_pairs(observations, max_days=12.5),
                references=reference_rows(_load(files['references'], root), 'acquisition_utc', peak), event=event,
                decision=k['decision'], interpretation=k['interpretation'], sources=list(files.values())))


def mark_event_span(case):
    event = case['event']['time']
    for p in case['pairs'] + case['consecutive']:
        p['spans_event'] = None if event is None else bool(p['before'] < event < p['after'])
    return case


def case_summary(case):
    refs = case['references']
    event = case['event']['time']
    post = [o for o in case['observations'] if event and o['time'] > event]
    return dict(nisar_acquisitions=len(case['observations']), compatible_pairs=len(case['pairs']),
                twelve_day_pairs=len(case['consecutive']),
                full_coverage_pairs=sum(p['coverage'] >= .99 for p in case['pairs']),
                optical_inspected=len(refs), optical_usable=sum(r['usable'] for r in refs),
                optical_any_valid=sum(r['valid_fraction'] > 0 for r in refs),
                first_post_event_hours=(post[0]['time'] - event).total_seconds() / 3600 if post else None)
