"""Read-only provenance for saved case comparisons; no new evaluation or calibration."""
import json
from datetime import datetime, timezone
from pathlib import Path

from rasterio.transform import Affine, array_bounds
from rasterio.warp import transform_bounds
from src.evidence_scope import case_records, ROOT
from src.water_change import pixel_area_km2
from rasterio.crs import CRS


def _read(path):
    return json.loads((ROOT / 'data/flood_validation' / path).read_text())


def reference_details(product_id, nisar_time, scans):
    """Acquisition timestamp, never production timestamp. Missing metadata stays missing."""
    row = next((r for r in scans if r.get('granule') == product_id and r.get('status') == 'read'), None)
    if row is None:
        return dict(product_id=product_id, acquired_utc=None, offset_hours=None, metadata_missing=True)
    acquired = datetime.strptime(row['acquired_utc'], '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
    return dict(product_id=product_id, acquired_utc=acquired.isoformat(),
                offset_hours=(acquired - datetime.fromisoformat(nisar_time)).total_seconds() / 3600,
                native_resolution_m=abs(row['transform'][0]), reference_window_pixels=row['pixels'],
                reference_window_valid_fraction=row['valid_fraction'],
                validity_includes_partial=True, window_outside_file=row['window_outside_file'])


def primary_evaluations():
    """Eight primary rows, each with its own evaluated mask denominator and references."""
    boot = _read('bootstrap_ab/results.json')
    scans = _read('reference/scan.json')['scenes']
    records = []
    for stage, record in case_records().items():
        n = record['nisar']; tr = Affine(*n['transform'])
        cell = pixel_area_km2(CRS.from_user_input(n['crs']), tr)
        for row in record['rows']:
            if not (row.get('variant') == 'HH' and 'TP' in row and
                    row['threshold_set'].startswith(('PRIMARY', 'frozen default'))):
                continue
            point = row; ci = row.get('ci95', {})
            if stage in ('a', 'b'):
                saved = boot['results'][stage]['primary_rows'][row['outcome'] + ' | ' + row['reference']]
                point, ci = saved['point'], saved['ci95']
            change = row['outcome'].startswith('new')
            ref_type = row['reference'].split()[0]
            roles = ['pre', 'during'] if change else ['during']
            refs = [reference_details(record['references'][ref_type + '_' + role],
                                     n['times'][0 if role == 'pre' else 1], scans) for role in roles]
            evaluated = sum(point[k] for k in ('TP', 'FP', 'FN', 'TN'))
            records.append(dict(stage=stage, outcome=row['outcome'], reference_type=ref_type,
                metrics={k: point[k] for k in ('precision', 'recall', 'F1', 'IoU')}, ci95=ci,
                counts={k: point[k] for k in ('TP', 'FP', 'FN', 'TN', 'invalid')},
                evaluated_pixels=evaluated, evaluated_area_km2=evaluated*cell,
                evaluated_fraction_of_grid=evaluated/(evaluated+point['invalid']),
                nisar=n, references=refs,
                bounds_wgs84=list(transform_bounds(n['crs'], 'EPSG:4326', *array_bounds(*n['grid_shape'], tr))),
                source_files=[f'data/flood_validation/step2{stage}/metrics.json'] +
                    (['data/flood_validation/bootstrap_ab/results.json'] if stage in ('a', 'b') else [])))
    return records


def negative_controls():
    record = _read('step2d/metrics.json')
    scans = _read('reference/scan.json')['scenes']
    result = []
    for track, r in record['tracks'].items():
        row = next(x for x in record['rows'] if x['scope'].endswith(track))
        ids = r['product_ids'][:2]
        times = [datetime.strptime(p.split('_')[11], '%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc).isoformat() for p in ids]
        refs = []
        for stamp, when in zip(('20260908T230013Z', '20260919T230839Z'), times):
            scan = next(x for x in scans if x.get('site') == 'thailand_prachinburi'
                        and x.get('product') == 'S1' and x.get('acquired_utc') == stamp)
            refs.append(reference_details(scan['granule'], when, scans))
        count = sum(row[k] for k in ('TP', 'FP', 'FN', 'TN'))
        result.append(dict(track=track, nisar_product_ids=ids, nisar_times=times, references=refs,
            candidate_area_km2=r['tier_A']['new_water_km2_before_before'],
            disagreement_area_km2=r['tier_B']['false_new_water_km2'],
            radar_valid_pixels=r['directions_before_before']['all valid']['pixels'],
            radar_valid_area_km2=r['directions_before_before']['all valid']['pixels']*0.0001,
            evaluated_pixels=count, evaluated_area_km2=count*0.0001,
            evaluated_fraction_of_grid=count/(count+row['invalid']),
            coregistration=r['coregistration'], source_file='data/flood_validation/step2d/metrics.json'))
    return result
