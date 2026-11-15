"""Phase 2 gate: HH and HV change for the original Louisiana pair, written to data/hv/.

No network access. Inputs are the verified cached HH subsets (data/subsets)
and the verified cached HVHV windows (data/polarization_analysis/raw), both
real bounded reads from earlier phases. Existing outputs are never modified;
if data/hv/hv_signal_assessment.json exists the script exits unchanged.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio

from scripts.detect_water_change import load_cached, save_raster
from src.change_compass import (DIRECTORY, PAIR_DATES, GROUP, read_raw_hv, pair_change, lag_correlation,
                                distribution, region_summary, sha256)

LAGS = (1, 3, 5, 10, 20)


def histogram_figure(hh, hv):
    bins = np.arange(-8, 8.01, 0.1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), layout='constrained', sharex=True)
    for ax, values, name, color in ((axes[0], hh, 'HH', '#007f83'), (axes[1], hv, 'HV', '#a04c83')):
        inside = values[(values >= bins[0]) & (values <= bins[-1])]
        ax.hist(inside, bins=bins, color=color, alpha=.85)
        ax.axvline(0, color='#555', lw=.8)
        ax.axvline(np.median(values), color='#12334a', ls='--', label=f'median {np.median(values):+.2f} dB')
        ax.set_title(f'Δ{name} · 3 July − 21 June 2026 · {values.size:,} pixels '
                     f'({100 * (values.size - inside.size) / values.size:.2f}% outside ±8 dB)', fontsize=9)
        ax.set_xlabel(f'Δ{name} (dB), filtered, after − before'); ax.legend(fontsize=8)
    axes[0].set_ylabel('Pixel count (spatially dependent)')
    fig.suptitle('Real NISAR GCOV Louisiana AOI · descriptive change distributions, not a classification', fontsize=10)
    return fig


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overwrite', action='store_true',
                        help='Rewrite this script\'s own data/hv outputs (never touches any other folder).')
    args = parser.parse_args(argv)
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    report_path = DIRECTORY / 'hv_signal_assessment.json'
    if report_path.exists() and not args.overwrite:
        print('data/hv results already exist; left unchanged (use --overwrite to regenerate them).')
        return 0
    manifest = json.loads((ROOT / 'data/nisar_manifest.json').read_text())
    previous = json.loads((ROOT / 'data/nisar_visualization_report.json').read_text())
    items = sorted(manifest['observations'], key=lambda p: p['start_time_utc'])
    if tuple(i['start_time_utc'][:10] for i in items) != PAIR_DATES:
        raise ValueError('Manifest dates differ from the expected pair.')
    hh_stack, hv_stack, sources, grid = [], [], [], None
    for item in items:
        date = item['start_time_utc'][:10]
        hh, hh_valid, hh_grid, hh_meta = load_cached(item, previous)  # existing verified HH loader
        hv, hv_grid, hv_meta = read_raw_hv(date)
        if hv_meta['product_id'] != item['product_id']:
            raise ValueError('HH and HV windows come from different products.')
        if (hv_grid['crs'] != hh_grid['crs'] or hv_grid['transform'] != hh_grid['transform']
                or tuple(hv_grid['shape']) != tuple(hh_grid['shape'])):
            raise ValueError('HH and HV windows are not on the same native grid; review before processing.')
        grid = grid or hh_grid
        hh_stack.append(np.where(hh_valid, hh, np.nan)); hv_stack.append(hv)
        hh_path = ROOT / 'data/subsets' / f'nisar_hhhh_{date}.tif'
        hv_path = ROOT / 'data/polarization_analysis/raw' / f'hvhv_{date}.tif'
        sources.append(dict(date=date, product_id=item['product_id'], acquisition_utc=item['start_time_utc'],
                            HH=dict(path=str(hh_path.relative_to(ROOT)), layer=GROUP + '/HHHH', sha256=sha256(hh_path)),
                            HV=dict(path=str(hv_path.relative_to(ROOT)), layer=GROUP + '/HVHV', sha256=sha256(hv_path),
                                    original_range_bytes_read=hv_meta.get('range_bytes_read'))))
    pair = pair_change(np.stack(hh_stack), np.stack(hv_stack))
    valid = pair['valid']; hh = pair['HH_delta'][valid]; hv = pair['HV_delta'][valid]

    # Cross-check against the earlier Phase 3 polarization output (must agree).
    with rasterio.open(ROOT / 'data/polarization_analysis/two_date/before_after_delta_db.tif') as src:
        earlier = src.read()[:2].astype(float)
    agree = [float(np.nanmax(np.abs(earlier[i][valid] - d[valid]))) for i, d in enumerate((pair['HH_delta'], pair['HV_delta']))]
    if max(agree) > 1e-4:
        raise ValueError('New HH/HV change disagrees with the earlier polarization output.')

    hv_levels = [distribution(pair['HV_db'][i][valid]) for i in (0, 1)]
    with rasterio.open(ROOT / 'data/water_change/water_change_classes.tif') as src:
        classes = src.read(1)
    class_names = {1: 'persistent_water_candidate', 2: 'new_water_candidate', 3: 'receded_water_candidate', 4: 'other_valid_surface'}
    class_rows = {}
    for code, name in class_names.items():
        s = region_summary(pair['HH_delta'], pair['HV_delta'], classes == code, hv_db=pair['HV_db'])
        class_rows[name] = dict(pixels=s['pixels'], median_dHH_db=s['HH']['median'], median_dHV_db=s['HV']['median'],
                                hv_dark_level=s['hv_dark_level'])
    indicators = dict(
        pixels=int(valid.sum()),
        HH_change=distribution(hh), HV_change=distribution(hv),
        pearson_r_dHH_dHV=float(np.corrcoef(hh, hv)[0, 1]),
        lag_autocorrelation={f'{k}px_{10 * k}m': dict(HH=lag_correlation(pair['HH_delta'], valid, k),
                                                     HV=lag_correlation(pair['HV_delta'], valid, k)) for k in LAGS},
        filtered_HV_level_db={PAIR_DATES[i]: hv_levels[i] for i in (0, 1)},
        filtered_HV_scene_p1_db={PAIR_DATES[i]: float(np.percentile(pair['HV_db'][i][valid], 1)) for i in (0, 1)},
        by_baseline_class=class_rows,
        noise_floor='not available: NISAR GCOV noise-equivalent layers are documented in linear DN² and a verified '
                    'DN²-to-gamma-0 conversion was not established (see data/scientific_diagnostics/REPORT.md); '
                    'noiseCorrectionApplied=False in both products.')
    lag5 = indicators['lag_autocorrelation']['5px_50m']['HV']
    verdict = dict(
        hv_scene_scale='usable with caution',
        evidence=[f"ΔHV is spatially structured beyond the 3×3 filter footprint: lag-5 px (50 m) autocorrelation "
                  f"{lag5[0]:.2f}/{lag5[1]:.2f} (columns/rows), compared with "
                  f"{indicators['lag_autocorrelation']['5px_50m']['HH'][0]:.2f} for ΔHH. Independent pixel noise would be near 0; "
                  "a smooth large-scale pattern (e.g. incidence-angle or calibration ramp) could also contribute.",
                  f"ΔHV and ΔHH are positively correlated (r = {indicators['pearson_r_dHH_dHV']:.2f}); speckle in the two "
                  "channels is largely independent, so part of the change is shared.",
                  f"Median ΔHV is {indicators['HV_change']['median']:+.2f} dB vs ΔHH {indicators['HH_change']['median']:+.2f} dB; "
                  f"IQR {indicators['HV_change']['p25']:+.2f}…{indicators['HV_change']['p75']:+.2f} dB."],
        dark_pixel_warning=(f"In the darkest pixels HV may be floor-limited: new-water candidates have median filtered HV "
                            f"{class_rows['new_water_candidate']['hv_dark_level']['dates'][0]['region_median_db']:.1f} / "
                            f"{class_rows['new_water_candidate']['hv_dark_level']['dates'][1]['region_median_db']:.1f} dB, close to the "
                            f"scene's 1st percentile ({indicators['filtered_HV_scene_p1_db'][PAIR_DATES[0]]:.1f} / "
                            f"{indicators['filtered_HV_scene_p1_db'][PAIR_DATES[1]]:.1f} dB), and their HV barely changes "
                            f"(median {class_rows['new_water_candidate']['median_dHV_db']:+.2f} dB) while HH drops "
                            f"{class_rows['new_water_candidate']['median_dHH_db']:+.2f} dB. A stable lower bound is consistent "
                            "with, but does not prove, a noise floor. HV change is weak evidence in such regions."),
        compass_policy='The Compass shows HV-based labels, flags regions whose median HV sits at/below the scene 5th '
                       'percentile on either date, and returns "inconclusive" for small or disagreeing change vectors.',
        not_established=['noise floor / HV SNR', 'cause of the scene-wide darkening', 'any land-cover or water truth'])
    outputs = {}
    tags = dict(product_ids=json.dumps([s['product_id'] for s in sources]), dates=json.dumps(PAIR_DATES),
                preprocessing='joint per-date HH/HV positive-finite mask; 3x3 mask-aware mean in linear power; 10*log10',
                units='dB', interpretation='Descriptive change only; not a classification')
    save_raster(DIRECTORY / 'pair_change_db.tif', [pair['HH_delta'], pair['HV_delta']],
                ['HH_after_minus_before_dB', 'HV_after_minus_before_dB'], grid, tags)
    save_raster(DIRECTORY / 'pair_filtered_db.tif', [pair['HH_db'][0], pair['HH_db'][1], pair['HV_db'][0], pair['HV_db'][1]],
                [f'HH_{PAIR_DATES[0]}_dB', f'HH_{PAIR_DATES[1]}_dB', f'HV_{PAIR_DATES[0]}_dB', f'HV_{PAIR_DATES[1]}_dB'], grid, tags)
    fig = histogram_figure(hh, hv); fig.savefig(DIRECTORY / 'change_histograms.png', dpi=140); plt.close(fig)
    for name in ('pair_change_db.tif', 'pair_filtered_db.tif', 'change_histograms.png'):
        outputs[name] = sha256(DIRECTORY / name)
    counts, edges = np.histogram(np.clip(hh, -8, 8), bins=np.arange(-8, 8.01, 0.5))
    counts_v, _ = np.histogram(np.clip(hv, -8, 8), bins=edges)
    report = dict(status='success', created_utc=datetime.now(timezone.utc).isoformat(), network_access_used=False,
                  pair=PAIR_DATES, sources=sources, crs=str(grid['crs']), transform=list(grid['transform'])[:6],
                  shape=list(grid['shape']), agreement_with_polarization_two_date_max_abs_db=dict(HH=agree[0], HV=agree[1]),
                  histogram_0p5db_clipped_pm8=dict(edges=edges.tolist(), HH=counts.tolist(), HV=counts_v.tolist()),
                  indicators=indicators, verdict=verdict, output_sha256=outputs)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    sidecar = dict(description='Sidecar for pair_change_db.tif and pair_filtered_db.tif', pair=PAIR_DATES,
                   sources=sources, output_sha256={k: v for k, v in outputs.items() if k.endswith('.tif')},
                   full_report='hv_signal_assessment.json')
    (DIRECTORY / 'pair_change_db.json').write_text(json.dumps(sidecar, indent=2) + '\n')
    print(json.dumps(dict(pixels=indicators['pixels'], HH=indicators['HH_change'], HV=indicators['HV_change'],
                          r=indicators['pearson_r_dHH_dHV'], lag=indicators['lag_autocorrelation'],
                          classes=class_rows, verdict=verdict), indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
