"""Deviation 4 bootstrap CIs (PRIMARY rows, stages a and b) and where false positives/negatives concentrate.

Recomputes the PRIMARY rows from the cached NISAR windows (no network read of NISAR; token not needed), checks that the
point estimates equal the saved stage outputs exactly, then adds 1 km spatial block-bootstrap 95 % intervals.
Context layers (public, no credentials): Copernicus DEM GLO-30 window (src/dem_reader.py) and one OpenStreetMap
Overpass snapshot (waterway=river lines; landuse residential/commercial/industrial/retail/farmland/aquaculture).
Writes only: data/flood_validation/context/thailand_prachinburi/, data/flood_validation/bootstrap_ab/.
"""
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import numpy as np
import requests
from rasterio.features import rasterize
from rasterio.transform import Affine
from rasterio.warp import reproject, transform_geom
from rasterio.enums import Resampling
from scipy.ndimage import distance_transform_edt, binary_dilation, binary_erosion
from shapely.geometry import LineString, Polygon, mapping

from src import flood_validation as fv
from src.dem_reader import read_dem_window, slope_degrees
from src.flood_classes import masks, OPEN
from src.live_engine import search_catalog, group_products, run_live
from src.podaac_reader import ByteBudget
from scripts.flood_step2 import aoi, reference

FV = ROOT / 'data/flood_validation'
SITE = 'thailand_prachinburi'
UA = {'User-Agent': 'NISAR-Change-Compass/1.0 (educational demo)'}
LANDUSE = ('residential', 'commercial', 'industrial', 'retail', 'farmland', 'aquaculture')


def cached_cube(track, frame, direction):
    region = aoi(SITE); c = region.centroid
    products, _ = search_catalog(c.y, c.x, date(2026, 9, 1), date(2026, 10, 15))
    g = next(g for g in group_products(products) if (g['key']['track'], g['key']['frame'], g['key']['direction'],
             g['key']['bandwidth']) == (track, frame, direction, '4005'))
    chosen = [p for p in g['products'] if p['date'] in ('2026-09-06', '2026-09-30')]
    with patch('src.nisar_data.open_frequency_a', side_effect=AssertionError('no NISAR network read here')):
        return run_live(chosen, c.y, c.x, 10.0, None, polygon=region)


def osm_snapshot(out):
    path = out / 'osm_overpass_snapshot.json'
    if path.exists():
        return json.loads(path.read_text())
    w, s, e, n = aoi(SITE).buffer(0.05).bounds
    q = (f'[out:json][timeout:90];(way["waterway"="river"]({s},{w},{n},{e});'
         f'way["landuse"~"^({"|".join(LANDUSE)})$"]({s},{w},{n},{e});'
         f'relation["landuse"~"^({"|".join(LANDUSE)})$"]({s},{w},{n},{e}););out geom tags;')
    r = requests.post('https://overpass-api.de/api/interpreter', data={'data': q}, headers=UA, timeout=120)
    r.raise_for_status()
    snap = dict(fetched_utc=datetime.now(timezone.utc).isoformat(), query=q, source='OpenStreetMap contributors, ODbL',
                elements=r.json()['elements'])
    path.write_text(json.dumps(snap) + '\n')
    return snap


def layers(grid, out):
    shape_, t, crs = grid['shape'], Affine(*grid['transform']), grid['crs']
    snap = osm_snapshot(out)
    rivers, landuse = [], {k: [] for k in LANDUSE}
    for el in snap['elements']:
        tags = el.get('tags', {})
        if el['type'] == 'way' and 'geometry' in el:
            coords = [(p['lon'], p['lat']) for p in el['geometry']]
            if tags.get('waterway') == 'river' and len(coords) > 1:
                rivers.append(transform_geom('EPSG:4326', crs, mapping(LineString(coords))))
            elif tags.get('landuse') in landuse and len(coords) > 3:
                landuse[tags['landuse']].append(transform_geom('EPSG:4326', crs, mapping(Polygon(coords))))
        elif el['type'] == 'relation' and tags.get('landuse') in landuse:
            for m in el.get('members', []):
                if m.get('role') == 'outer' and 'geometry' in m and len(m['geometry']) > 3:
                    landuse[tags['landuse']].append(transform_geom('EPSG:4326', crs, mapping(
                        Polygon([(p['lon'], p['lat']) for p in m['geometry']]))))
    river_px = rasterize(rivers, shape_, transform=t, fill=0, default_value=1, all_touched=True).astype(bool) if rivers else np.zeros(shape_, bool)
    river_dist = distance_transform_edt(~river_px) * abs(t.a)
    lu = {k: (rasterize(v, shape_, transform=t, fill=0, default_value=1).astype(bool) if v else np.zeros(shape_, bool))
          for k, v in landuse.items()}
    dem = read_dem_window(14.0541, 101.3724, aoi(SITE), ByteBudget())
    slope = slope_degrees(dem['height'], dem['transform'])
    slope_g = np.full(shape_, np.nan); height_g = np.full(shape_, np.nan)
    reproject(slope, slope_g, src_transform=Affine(*dem['transform']), src_crs=dem['crs'], dst_transform=t, dst_crs=crs,
              resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
    reproject(dem['height'], height_g, src_transform=Affine(*dem['transform']), src_crs=dem['crs'], dst_transform=t, dst_crs=crs,
              resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
    np.savez_compressed(out / 'layers_on_nisar_grid.npz', river_distance_m=river_dist.astype(np.float32),
                        slope_deg=slope_g.astype(np.float32), height_m=height_g.astype(np.float32),
                        **{f'landuse_{k}': v for k, v in lu.items()})
    meta = dict(dem_source=dem['source'], dem_bytes_read=dem['bytes_read'], osm_fetched_utc=snap['fetched_utc'],
                river_lines=len(rivers), landuse_polygons={k: len(v) for k, v in landuse.items()}, grid=grid)
    return dict(river_distance=river_dist, slope=slope_g, height=height_g, landuse=lu, meta=meta)


def shares(mask, cats, base):
    n = int(mask.sum())
    return dict(pixels=n, **{k: (float((mask & v).sum()) / n if n else None) for k, v in cats.items()},
                **{f'baseline_{k}': float((base & v).sum()) / max(1, int(base.sum())) for k, v in cats.items()})


def main():
    ctx_dir = FV / 'context' / SITE; boot_dir = FV / 'bootstrap_ab'
    if (boot_dir / 'results.json').exists():
        print('bootstrap_ab exists; left unchanged.'); return 0
    ctx_dir.mkdir(parents=True, exist_ok=True); boot_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    lay = None
    for stage, track, frame, d in (('a', '004', '081', 'D'), ('b', '011', '009', 'A')):
        cube = cached_cube(track, frame, d)
        prep = fv.preprocess(cube)
        grid = dict(shape=prep['valid'].shape, transform=cube['transform'], crs=cube['crs'])
        lay = lay or layers(grid, ctx_dir)
        s1_pre = reference(SITE, 'S1', '20260908T230013Z', grid); s1_dur = reference(SITE, 'S1', '20261001T230839Z', grid)
        hls = reference(SITE, 'HLS', '20261002T033141Z', grid)
        saved = {(r['outcome'], r.get('reference')): r for r in json.loads((FV / f'step2{stage}/metrics.json').read_text())['rows']
                 if r.get('variant') == 'HH' and ('default' in r['threshold_set'] or 'PRIMARY' in r['threshold_set']) and 'TP' in r}
        pred_new = fv.nisar_new_water(prep, 0, 1, 'HH', fv.DEFAULT_HH, None)
        pred_pres = fv.nisar_presence(prep, 1, 'HH', fv.DEFAULT_HH, None)
        pos_n, neg_n = fv.reference_new_water(s1_pre['codes'], s1_dur['codes'], 'S1')
        rows = {}
        for key, pred, (pos, neg, _) in (
                (('new open water (during minus pre)', 'S1 primary'), pred_new, (pos_n, neg_n, None)),
                (('open water presence (during)', 'S1 primary'), pred_pres, fv.reference_presence(s1_dur['codes'], 'S1')),
                (('open water presence (during)', 'HLS sensitivity'), pred_pres, fv.reference_presence(hls['codes'], 'HLS'))):
            point = fv.confusion(pred, pos, neg, prep['valid'])
            same = all(point[k] == saved[key][k] for k in ('TP', 'FP', 'FN', 'TN'))
            rows[' | '.join(key)] = dict(point=point, matches_saved_point_estimate=same,
                                         ci95=fv.block_bootstrap(pred, pos, neg, prep['valid'], int(fv.BOOT_BLOCK_M / abs(cube['transform'][0]))))
            if not same:
                raise SystemExit(f'Stage {stage}: recomputed point estimate differs from saved output for {key}')
        # where do FP / FN of the PRIMARY new-water row concentrate?
        evaluated = prep['valid'] & (pos_n | neg_n)
        edge = binary_dilation(pos_n, iterations=6) & ~binary_erosion(pos_n, iterations=6)       # +-60 m of S1 new-water boundary
        hls_open = masks(hls['codes'], 'HLS')[OPEN]
        cats = {'river channel (<=100 m of OSM river)': lay['river_distance'] <= 100,
                'near river (100 m - 1 km)': (lay['river_distance'] > 100) & (lay['river_distance'] <= 1000),
                'S1 flood edge (+-60 m)': edge, 'OSM built-up (residential/commercial/industrial/retail)':
                lay['landuse']['residential'] | lay['landuse']['commercial'] | lay['landuse']['industrial'] | lay['landuse']['retail'],
                'OSM farmland': lay['landuse']['farmland'], 'OSM aquaculture': lay['landuse']['aquaculture'],
                'slope > 5 deg': lay['slope'] > 5, 'HLS 10-02 open water': hls_open}
        fp = pred_new & neg_n & prep['valid']; fn = ~pred_new & pos_n & prep['valid']
        after, before = prep['HH'][1], prep['HH'][0]
        mechanisms = dict(
            FN_after_not_dark=float((fn & (after > fv.DEFAULT_HH)).sum()) / max(1, fn.sum()),
            FN_already_dark_before=float((fn & (before <= fv.DEFAULT_HH)).sum()) / max(1, fn.sum()),
            FN_change_below_3dB=float((fn & (np.abs(after - before) < fv.MIN_CHANGE)).sum()) / max(1, fn.sum()),
            FP_median_dHH_db=float(np.median((after - before)[fp])) if fp.any() else None)
        results[stage] = dict(track=f'{track} {d}', primary_rows=rows,
                              new_water_FP=shares(fp, cats, evaluated), new_water_FN=shares(fn, cats, evaluated),
                              new_water_TP=shares(pred_new & pos_n & prep['valid'], cats, evaluated), mechanisms=mechanisms)
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(), deviation=4,
                  bootstrap=dict(block_m=fv.BOOT_BLOCK_M, resamples=fv.BOOT_N, seed=fv.BOOT_SEED, interval='2.5/97.5 percentiles'),
                  context=lay['meta'], results=results)
    (boot_dir / 'results.json').write_text(json.dumps(report, indent=1, default=str) + '\n')
    for d in (boot_dir, ctx_dir):
        files = sorted(p for p in d.iterdir() if p.is_file() and p.name != 'sidecar.json')
        (d / 'sidecar.json').write_text(json.dumps(dict(outputs_sha256={p.name: fv.sha256(p) for p in files},
            code_sha256={p: fv.sha256(ROOT / p) for p in ('scripts/flood_bootstrap_context.py', 'src/flood_validation.py', 'src/dem_reader.py')}),
            indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
