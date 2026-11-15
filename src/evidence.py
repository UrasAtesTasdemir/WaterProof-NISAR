"""Evidence & limitations checklist: combines EXISTING saved evidence into
'no concern from this check' / caution / unknown (internal keys: pass / warn / unknown).

Nothing is recomputed here. Each item reads a saved report from an earlier
phase, applies a stated rule, and returns the numbers it used plus the file it
came from. This is an evidence checklist, not validation and not a confidence or accuracy
score. Text comes from the translation layer (``lang``, English by default);
sentences copied from saved English reports are labelled as such in Turkish.
"""
import csv
import json
from datetime import datetime
from pathlib import Path

from src.i18n import t, num, integer, percent, saved_text

ROOT = Path(__file__).resolve().parents[1]
PASS, WARN, UNKNOWN = 'pass', 'warn', 'unknown'

SOURCES = {
    'reliability': 'data/reliability/results.json',
    'singletons': 'data/reliability/singleton_statistics.json',
    'quality': 'data/scientific_quality_check/quality_diagnostics.json',
    'threshold_csv': 'data/scientific_quality_check/threshold_sensitivity.csv',
    'validation': 'data/validation/validation_results.json',
    'same_day': 'data/scientific_quality_check/independent_reference_check.json',
    'pair_selection': 'data/pair_selection/pair_ranking.json',
    'quality_metadata': 'data/scientific_diagnostics/quality_metadata.json',
    'hv': 'data/hv/hv_signal_assessment.json',
    'kerrville': 'data/kerrville_feasibility/feasibility.json',
    'kerrville_refs': 'data/kerrville_feasibility/reference_windows.json',
}
RULE_KEYS = ('offset', 'threshold', 'singletons', 'waterways', 'reference', 'registration', 'quality_mask', 'cross_pol', 'timing', 'coverage')
# Stated rules (exploratory, chosen to be conservative; not universal standards). English copy for reference.
RULES = {key: t(f'ev.rule.{key}', lang='en') for key in RULE_KEYS}


def _load(name, root=ROOT):
    path = Path(root) / SOURCES[name]
    if path.suffix == '.csv':
        with path.open() as handle:
            return list(csv.DictReader(handle))
    return json.loads(path.read_text())


def item(key, title, status, finding, evidence, source, lang='en'):
    if status not in (PASS, WARN, UNKNOWN):
        raise ValueError('Unknown status.')
    rule = t(f'ev.rule.{key}', lang=lang) if f'ev.rule.{key}' in RULES_KEYS_SET else ''
    return dict(key=key, title=title, status=status, finding=finding, evidence=evidence, rule=rule, source=source)


RULES_KEYS_SET = {f'ev.rule.{k}' for k in RULE_KEYS}


def louisiana_checklist(root=ROOT, lang='en'):
    """Checklist for the Louisiana June21→July3 baseline (−16 dB, 3 dB, singleton filter OFF)."""
    T = lambda key, **v: t(key, lang=lang, **v)
    n = lambda x, d=2, sign=False: num(x, d, sign, lang=lang)
    items = []
    rel = _load('reliability', root)
    base = rel['darkening_scenarios'][0]['baseline_expansion_pixels_still_candidates']
    full = next(s for s in rel['darkening_scenarios'] if s['fraction_of_measured_median_removed'] == 1)
    survive = full['baseline_expansion_pixels_still_candidates'] / base
    items.append(item('offset', T('ev.title.offset'), WARN if survive < .5 else PASS,
        T('ev.find.offset', median=n(rel['measured_median_delta_db']), kept=full['baseline_expansion_pixels_still_candidates'], base=base,
          share=percent(survive, 0, lang), area=n(full['expansion_km2'], 4), area0=n(rel['darkening_scenarios'][0]['expansion_km2'], 4)),
        dict(median_delta_db=rel['measured_median_delta_db'], surviving_fraction=survive,
             scenarios=rel['darkening_scenarios']), SOURCES['reliability'], lang))

    rows = {float(r['water_threshold_db']): r for r in _load('threshold_csv', root)}
    area = {key: float(rows[key]['expansion_km2']) for key in rows}
    centre = area[-16.0]; low, high = area[-14.0], area[-18.0]
    factor = max(low, high) / centre if centre else float('inf')
    factor_down = centre / min(low, high) if min(low, high) else float('inf')
    worst = max(factor, factor_down)
    items.append(item('threshold', T('ev.title.threshold'), WARN if worst > 2 else PASS,
        T('ev.find.threshold', a14=n(area[-14.0], 4), a16=n(centre, 4), a18=n(area[-18.0], 4), a20=n(area[-20.0], 4), worst=n(worst, 1)),
        dict(expansion_km2_by_threshold=area), SOURCES['threshold_csv'], lang))

    single = _load('singletons', root); quality = _load('quality', root)
    total = rel['waterway_context']['default']['expansion']['within_30m_pixels'] + rel['waterway_context']['default']['expansion']['beyond_30m_pixels']
    share = single['count'] / total
    comp = quality['connected_components']
    items.append(item('singletons', T('ev.title.singletons'), WARN if share > .10 else PASS,
        T('ev.find.singletons', count=single['count'], total=total, share=percent(share, 1, lang), groups=comp['component_count'],
          largest=comp['largest_component_pixels'], m2=comp['largest_component_pixels'] * 100),
        dict(singletons=single['count'], expansion_pixels=total, components=comp), SOURCES['singletons'], lang))

    near = rel['waterway_context']['default']['expansion']
    frac = near['within_30m_pixels'] / total
    items.append(item('waterways', T('ev.title.waterways'), WARN if frac > .5 else PASS,
        T('ev.find.waterways', near=near['within_30m_pixels'], total=total, share=percent(frac, 0, lang)),
        dict(within_30m=near['within_30m_pixels'], beyond_30m=near['beyond_30m_pixels']), SOURCES['reliability'], lang))

    val = _load('validation', root); pairs = _load('pair_selection', root)
    top = max(val['reference_inventory'], key=lambda r: r['valid_coverage_fraction'])
    same_day = [o for o in _load('same_day', root)['observations'] if o.get('same_day')]
    same_text = ', '.join(T('ev.same_day_item', date=o['acquisition_utc'][:10],
                            share=percent(o['usable_water_or_nonwater_pixels'] / o['aoi_pixel_centers'], 0, lang))
                          for o in same_day) or T('ev.none_inspected')
    best = top['valid_coverage_fraction']
    items.append(item('reference', T('ev.title.reference'), PASS if val['quantitative_validation_possible'] else UNKNOWN,
        T('ev.find.reference', reason=saved_text(val['reason'], lang), same=same_text, collection=top['collection'],
          date=top['acquisition_utc'][:10], best=percent(best, 0, lang),
          hours=n(min(abs(h) for h in top['time_offset_hours_from_nisar'].values()), 0), decision=saved_text(pairs['decision'], lang)),
        dict(quantitative_validation_possible=val['quantitative_validation_possible'], references=len(val['reference_inventory']),
             policy=val['eligibility_policy']), SOURCES['validation'], lang))

    reg = quality['integer_registration_diagnostic']['best']
    items.append(item('registration', T('ev.title.registration'),
        PASS if (reg['row_shift'], reg['column_shift']) == (0, 0) else WARN,
        T('ev.find.registration', row=reg['row_shift'], col=reg['column_shift'], corr=n(reg['gradient_correlation']),
          limitation=saved_text(quality['integer_registration_diagnostic']['limitation'], lang)),
        dict(best=reg), SOURCES['quality'], lang))

    meta = _load('quality_metadata', root)
    codes = [o['layers']['mask'].get('observed_common_codes', {}) for o in meta['observations']]
    ok = all(set(c) == {'1'} for c in codes) and len(codes) == 2
    listing = '; '.join(f"{o['date']}: " + ', '.join(T('ev.code_item', code=c, count=integer(cnt, lang)) for c, cnt in sorted(cc.items()))
                        for o, cc in zip(meta['observations'], codes))
    items.append(item('quality_mask', T('ev.title.quality_mask'), PASS if ok else WARN,
        T('ev.find.quality_mask', listing=listing), dict(codes=codes), SOURCES['quality_metadata'], lang))

    hv_path = Path(root) / SOURCES['hv']
    if hv_path.exists():
        hv = json.loads(hv_path.read_text())
        new = hv['indicators']['by_baseline_class']['new_water_candidate']
        items.append(item('cross_pol', T('ev.title.cross_pol'), WARN if new['hv_dark_level']['flag'] else UNKNOWN,
            T('ev.find.cross_pol', dhh=n(new['median_dHH_db'], 2, True), dhv=n(new['median_dHV_db'], 2, True),
              d0=n(new['hv_dark_level']['dates'][0]['region_median_db'], 1), d1=n(new['hv_dark_level']['dates'][1]['region_median_db'], 1)),
            dict(new_water_candidate=new), SOURCES['hv'], lang))
    else:
        items.append(item('cross_pol', T('ev.title.cross_pol'), UNKNOWN, T('ev.find.cross_pol_missing'), {}, SOURCES['hv'], lang))
    return items


def kerrville_checklist(root=ROOT, lang='en'):
    """No change map exists for Kerrville; only availability-type evidence is reported."""
    T = lambda key, **v: t(key, lang=lang, **v)
    n = lambda x, d=2: num(x, d, lang=lang)
    k = _load('kerrville', root); refs = _load('kerrville_refs', root)
    usable = [r for r in refs if r.get('valid_fraction', 0) > 0]
    best = max(refs, key=lambda r: r.get('valid_fraction', 0))
    full = [p for p in k['compatible_12day_pairs'] if p['nominal_common_aoi_coverage_fraction'] > .99]
    obs = k['gauge_timing']['observations'][0]
    peak = datetime.fromisoformat(k['gauge_timing']['peak']['dateTime'])
    best_time = datetime.fromisoformat(best['acquisition_utc'].replace('Z', '+00:00'))
    relation = T('ev.before') if best_time < peak else T('ev.after')
    usable_after = [r for r in usable if datetime.fromisoformat(r['acquisition_utc'].replace('Z', '+00:00')) > peak]
    if usable_after:
        top_after = max(usable_after, key=lambda r: r['valid_fraction'])
        after_text = T('ev.after_item', share=percent(top_after['valid_fraction'], 3, lang), date=top_after['acquisition_utc'][:10])
    else:
        after_text = T('ev.none_valid')
    na = T('ev.find.not_available')
    items = [item(key, T(f'ev.title.{key}'), UNKNOWN, na, {}, SOURCES['kerrville'], lang)
             for key in ('offset', 'threshold', 'singletons', 'waterways')]
    items += [
        item('reference', T('ev.title.reference'), UNKNOWN,
             T('ev.find.k_reference', inspected=len(refs), valid=len(usable), best=percent(best.get('valid_fraction', 0), 1, lang),
               date=best['acquisition_utc'][:10], relation=relation, after=after_text, hits=k['DSWx_S1_hits'],
               decision=saved_text(k['decision'], lang)),
             dict(inspected=len(refs), with_valid_pixels=len(usable)), SOURCES['kerrville_refs'], lang),
        item('timing', T('ev.title.timing'), WARN,
             T('ev.find.timing', hours=n(obs['hours_after_gauge_peak'], 1), station=k['gauge_timing']['station'],
               stage=obs['nearest_stage_ft']),
             dict(observation=obs), SOURCES['kerrville'], lang),
        item('coverage', T('ev.title.coverage'), PASS if full else WARN,
             T('ev.find.coverage', pairs=len(k['compatible_12day_pairs']), full=len(full),
               share=percent(min(p['nominal_common_aoi_coverage_fraction'] for p in k['compatible_12day_pairs']), 0, lang)),
             dict(pairs=k['compatible_12day_pairs']), SOURCES['kerrville'], lang),
    ]
    return items


def summarize(items, lang='en'):
    counts = {s: sum(i['status'] == s for i in items) for s in (PASS, WARN, UNKNOWN)}
    reference = next((i for i in items if i['key'] == 'reference'), None)
    if reference and reference['status'] != PASS:
        headline = t('ev.head.exploratory', lang=lang)
    elif counts[WARN]:
        headline = t('ev.head.concerns', lang=lang)
    else:
        headline = t('ev.head.none', lang=lang)
    if counts[WARN] >= 3:
        headline += ' ' + t('ev.head.several', lang=lang)
    return dict(counts=counts, headline=headline)
