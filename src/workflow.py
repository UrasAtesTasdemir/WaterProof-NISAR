"""Researcher workflow: one candidate, one date pair, one evidence list.

Assembles numbers that already exist (saved investigation regions, saved
robustness results, verified HH/HV cubes) plus the same descriptive Compass
rules. It adds no new science and makes no claims beyond the inputs; the
review note is built only from the context dictionary returned here.
"""
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio

from src.change_compass import region_summary, compass_reading, LABELS, DEFAULT_DEAD_ZONE_DB, MIN_PIXELS, label_text, reason_text
from src.i18n import t, num, integer
from src.polarization import load_polarization, compare_polarizations
from src.investigation import load_investigations
from src.robustness import ring_mask, ring_comparison
from src.water_change import pixel_area_km2

ROOT = Path(__file__).resolve().parents[1]
ROBUSTNESS = ROOT / 'data/robustness_v2'   # version 2: leave-one-date-out checks only the interval carrying the seed event
CONSISTENT, CAUTION, NEUTRAL, UNKNOWN = 'consistent', 'caution', 'neutral', 'unknown'
PAIR, BASELINE, CONTEXT = 'pair', 'baseline', 'context'
STATUSES = (CONSISTENT, CAUTION, NEUTRAL, UNKNOWN)
SCOPES = (PAIR, BASELINE, CONTEXT)


def status_text(status, lang='en'):
    return t(f'wf.status.{status}', lang=lang)


def scope_text(scope, lang='en'):
    return t(f'wf.scope.{scope}', lang=lang)


# English copies kept for callers that expect plain dictionaries.
STATUS_TEXT = {s: status_text(s) for s in STATUSES}
SCOPE_TEXT = {s: scope_text(s) for s in SCOPES}
NOISE_FLOOR_NOTE = t('wf.noise_floor_note', lang='en')
# Order in which a caution is reported as "the single most important uncertainty" (most decisive first).
UNCERTAINTY_PRIORITY = ('pattern', 'lodo', 'ring', 'region_size', 'hv', 'settings_a', 'settings_b', 'edge', 'time')
TOP5_SHARE = 2 / 3  # stated rule: candidate kept in the top 5 under at least two thirds of the settings variants


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_robustness(directory=ROBUSTNESS):
    """Saved robustness outputs (version 2 by default), verified against their sidecar."""
    directory = Path(directory)
    sidecar = json.loads((directory / 'sidecar.json').read_text())
    for name, digest in sidecar['outputs_sha256'].items():
        if _sha(directory / name) != digest:
            raise ValueError(f'{name} changed since it was written.')
    report = json.loads((directory / 'results.json').read_text())
    with (directory / report['files']['settings']).open() as handle:
        report['settings_rows'] = list(csv.DictReader(handle))
    return report


def load_inputs(root=ROOT):
    data = load_polarization(Path(root) / 'data/polarization_analysis/six_date')
    investigations = load_investigations()
    with rasterio.open(Path(root) / 'data/investigation_engine/region_labels.tif') as src:
        labels = src.read(1)
    from src.evidence import louisiana_checklist
    reference = {lang: next(i for i in louisiana_checklist(root, lang=lang) if i['key'] == 'reference') for lang in ('en', 'tr')}
    return dict(data=data, investigations=investigations, labels=labels, robustness=load_robustness(),
                independent_reference=reference)


def day(date):
    return datetime.fromisoformat(date[:10])


def pair_spans_gap(dates, first, second, gaps):
    a, b = day(dates[first]), day(dates[second])
    return [g for g in gaps if a <= day(g['start']) and day(g['end']) <= b]


def default_pair(region):
    return (region['seed_interval'], region['seed_interval'] + 1)


def build_context(inputs, candidate_id, first, second, dead_zone_db=DEFAULT_DEAD_ZONE_DB, lang='en'):
    T = lambda key, **v: t(key, lang=lang, **v)
    n = lambda x, d=2, sign=False: num(x, d, sign, lang=lang)
    data = inputs['data']; regions = inputs['investigations']['regions']; robust = inputs['robustness']
    if candidate_id not in [r['id'] for r in regions]:
        raise ValueError(T('wf.err.candidate'))
    dates = [o['date'] for o in data['report']['observations']]
    if not (0 <= first < second < len(dates)):
        raise ValueError(T('wf.err.pair'))
    region = next(r for r in regions if r['id'] == candidate_id)
    footprint = inputs['labels'] == candidate_id
    others = np.isin(inputs['labels'], [r['id'] for r in regions])
    pair = compare_polarizations(data, first, second)
    grid = data['grid']; cell = pixel_area_km2(grid['crs'], grid['transform'])
    summary = region_summary(pair['HH_delta'], pair['HV_delta'], footprint, cell, hv_db=data['HV'][[first, second]])
    scene = (pair['statistics']['median_HH_delta_db'], pair['statistics']['median_HV_delta_db'])
    reading = compass_reading(summary, scene, dead_zone_db, MIN_PIXELS)
    ring = ring_mask(footprint, data['common'], exclude=others)
    ring_row = ring_comparison(data['HH'][[first, second]], data['HV'][[first, second]], footprint & pair['valid'],
                               ring & pair['valid'], [dates[first], dates[second]])[0]
    rsum = next(s for s in robust['summary'] if s['candidate'] == candidate_id)
    lodo = robust['leave_one_date_out'][str(candidate_id)]
    variants = [r for r in robust['settings_rows'] if int(r['candidate']) == candidate_id]
    gaps = pair_spans_gap(dates, first, second, robust['acquisition_gaps'])
    days = (day(dates[second]) - day(dates[first])).days
    tau = n(dead_zone_db, 2).rstrip('0').rstrip(',.')

    evidence = []
    def add(ident, status, text, rule, scope=PAIR, short=None):
        evidence.append(dict(id=ident, topic=T(f'wf.topic.{ident}'), status=status, text=text, rule=rule, scope=scope,
                             short=short or text))
    title = label_text(reading['key'], lang=lang)
    if reading['key'] == 'inconclusive':
        add('pattern', CAUTION, T('wf.ev.pattern_none', reason=reason_text(reading['raw'], lang)), T('wf.rule.pattern_none'),
            short=T('wf.short.pattern_none'))
    elif not reading['agree']:
        add('pattern', CAUTION, T('wf.ev.pattern_differ', raw=label_text(reading['raw']['key'], lang=lang),
                                  relative=label_text(reading['relative']['key'], lang=lang)), T('wf.rule.pattern'),
            short=T('wf.short.pattern_differ'))
    else:
        add('pattern', CONSISTENT, T('wf.ev.pattern_agree', title=title), T('wf.rule.pattern'))
    contrast = ring_row['candidate_minus_ring_dHH_db']
    add('ring', CONSISTENT if abs(contrast) >= dead_zone_db else CAUTION,
        T('wf.ev.ring', cand=n(ring_row['candidate_dHH_db'], 2, True), ring=n(ring_row['ring_dHH_db'], 2, True),
          diff=n(contrast, 2, True), diff_hv=n(ring_row['candidate_minus_ring_dHV_db'], 2, True)),
        T('wf.rule.ring', tau=tau), short=T('wf.short.ring', diff=n(contrast, 2, True), tau=tau))
    in_top5 = rsum['variants_in_top5']; total = rsum['settings_variants']
    add('settings_a', CONSISTENT if in_top5 >= TOP5_SHARE * total else CAUTION,
        T('wf.ev.settings_a', top5=in_top5, total=total, r0=rsum['rank_range'][0], r1=rsum['rank_range'][1],
          p0=rsum['screened_pixels_range'][0], p1=rsum['screened_pixels_range'][1], pixels=region['pixels']),
        T('wf.rule.settings_a'), BASELINE, short=T('wf.short.settings_a', top5=in_top5, total=total))
    add('settings_b', CONSISTENT if rsum['variants_same_seed'] >= TOP5_SHARE * total else CAUTION,
        T('wf.ev.settings_b', same=rsum['variants_same_seed'], total=total, i0=n(rsum['iou_top5_range'][0]), i1=n(rsum['iou_top5_range'][1])),
        T('wf.rule.settings_b'), BASELINE, short=T('wf.short.settings_b', same=rsum['variants_same_seed'], total=total))
    failed = rsum['lodo_dates_not_notable']; untestable = rsum['lodo_dates_not_testable']
    lodo_text = T('wf.ev.lodo', kept=rsum['lodo_removals_still_notable'], total=rsum['lodo_removals'])
    if failed:
        lodo_text += T('wf.ev.lodo_failed', dates=', '.join(failed))
    if untestable:
        lodo_text += T('wf.ev.lodo_untestable', dates=', '.join(untestable))
    add('lodo', CONSISTENT if not failed else CAUTION, lodo_text + '.', T('wf.rule.lodo'), BASELINE,
        short=T('wf.short.lodo', dates=', '.join(failed)) if failed else None)
    dark = summary.get('hv_dark_level', {})
    add('hv', CAUTION if dark.get('flag') else NEUTRAL,
        T('wf.ev.hv_dark' if dark.get('flag') else 'wf.ev.hv_neutral') + ' ' + T('wf.noise_floor_note'), T('wf.rule.hv'),
        short=T('wf.short.hv'))
    add('time', CAUTION if gaps or days > 12 else CONSISTENT,
        (T('wf.ev.time_gap', days=days, gap=gaps[0]['days'], start=gaps[0]['start'], end=gaps[0]['end']) if gaps
         else T('wf.ev.time', days=days) + (T('wf.ev.time_long') if days > 12 else '')),
        T('wf.rule.time'), short=T('wf.short.time_gap', gap=gaps[0]['days']) if gaps else T('wf.short.time', days=days))
    if region['touches_processed_boundary']:
        add('edge', CAUTION, T('wf.ev.edge'), T('wf.rule.edge'))
    if summary.get('pixels', 0) < MIN_PIXELS:
        add('region_size', CAUTION, T('wf.ev.region_size', pixels=summary.get('pixels', 0), minimum=MIN_PIXELS), T('wf.rule.region_size'))
    reference = inputs['independent_reference']
    reference = reference.get(lang, reference.get('en')) if 'en' in reference else reference
    add('reference', UNKNOWN, reference['finding'], reference['rule'], CONTEXT, short=T('wf.short.reference'))

    questions = [T('wf.q.reference')]
    if not reading['agree']:
        questions.append(T('wf.q.scene'))
    if dark.get('flag'):
        questions.append(T('wf.q.hv'))
    if failed:
        questions.append(T('wf.q.lodo', dates=', '.join(failed)))
    if gaps:
        questions.append(T('wf.q.gap'))
    if in_top5 < TOP5_SHARE * total:
        questions.append(T('wf.q.settings'))
    questions.append(T('wf.q.alternatives'))
    from src.placebo import cached_results, for_candidate
    placebo = for_candidate(cached_results(), candidate_id)
    return dict(candidate=region, footprint_pixels=int(footprint.sum()), dates=dates, first=first, second=second, placebo=placebo,
                interval_days=days, gaps=gaps, summary=summary, scene=scene, reading=reading, ring=ring_row,
                robustness=dict(summary=rsum, lodo=lodo, variants=variants), evidence=evidence, open_questions=questions,
                dead_zone_db=dead_zone_db, product_ids=[o['product_id'] for o in data['report']['observations']],
                pair_valid=pair['valid'], HH_delta=pair['HH_delta'], footprint_mask=footprint, grid=grid, lang=lang)


def key_uncertainty(ctx):
    """The single most important uncertainty, taken from the evidence list (first caution by stated priority,
    otherwise the missing independent reference)."""
    cautions = {e['id']: e for e in ctx['evidence'] if e['status'] == CAUTION}
    for ident in UNCERTAINTY_PRIORITY:
        if ident in cautions:
            return cautions[ident]
    return next(e for e in ctx['evidence'] if e['id'] == 'reference')


def observation(ctx):
    """Two sentences: what was observed for the pair, and the most important uncertainty (both from the context)."""
    lang = ctx['lang']; s = ctx['summary']; d1, d2 = ctx['dates'][ctx['first']], ctx['dates'][ctx['second']]
    if s.get('pixels'):
        first = t('wf.obs.first', lang=lang, d1=d1, d2=d2, dhh=num(s['HH']['median'], 2, True, lang=lang),
                  dhv=num(s['HV']['median'], 2, True, lang=lang), pattern=label_text(ctx['reading']['key'], lang=lang))
    else:
        first = t('wf.obs.no_pixels', lang=lang, d1=d1, d2=d2)
    item = key_uncertainty(ctx)
    return first + ' ' + t('wf.obs.second', lang=lang, text=item['short'].rstrip('.'))


def _evidence_table(ctx, scope):
    lang = ctx['lang']
    rows = [e for e in ctx['evidence'] if e['scope'] == scope]
    if not rows:
        return []
    return ([t('wf.note.table_head', lang=lang), '|---|---|---|---|'] +
            [f"| {e['topic']} | {status_text(e['status'], lang)} | {e['text']} | {e['rule']} |" for e in rows] + [''])


def robustness_summary(ctx):
    """Exact saved counts, distinct from the selected-pair interpretation."""
    s = ctx['robustness']['summary']; lang = ctx['lang']
    all_settings = s['variants_in_top5'] == s['variants_same_seed'] == s['settings_variants']
    T = lambda key, **v: t(key, lang=lang, **v)
    return [T('ux.settings', label=T('ux.stable' if all_settings else 'ux.sensitive'),
              kept=s['variants_in_top5'], total=s['settings_variants'], same=s['variants_same_seed']),
            T('ux.dates', seed=s['seed'], kept=s['lodo_removals_still_notable'], total=s['lodo_removals'],
              failed=', '.join(s['lodo_dates_not_notable']) or T('common.none'),
              untestable=', '.join(s['lodo_dates_not_testable']) or T('common.none')),
            T('ux.temporary'), T('ux.reference')]


def investigation_action(ctx):
    """A proposed evidence request, never a claim that external data were found."""
    key = ctx['reading']['key']
    kind = ('insufficient' if key == 'inconclusive' else 'reference' if key == 'reference_dependent'
            else 'smooth' if key in ('smoother_surface', 'hh_darkening') else 'bright')
    r = ctx['candidate']
    values = dict(id=r['id'], d1=ctx['dates'][ctx['first']], d2=ctx['dates'][ctx['second']])
    question = t('ux.question.' + kind, lang=ctx['lang'], **values)
    values.update(lon=f"{r['representative_longitude']:.5f}", lat=f"{r['representative_latitude']:.5f}")
    action_key = 'ux.action.' + kind if kind in ('insufficient', 'reference') else 'ux.action'
    return question, t(action_key, lang=ctx['lang'], **values)


def review_note(ctx):
    """Markdown review note built only from the context (no new claims), in the context's language."""
    lang = ctx['lang']
    T = lambda key, **v: t(key, lang=lang, **v)
    n = lambda x, d=2, sign=False: num(x, d, sign, lang=lang)
    r = ctx['candidate']; s = ctx['summary']; rd = ctx['reading']; rs = ctx['robustness']['summary']
    d1, d2 = ctx['dates'][ctx['first']], ctx['dates'][ctx['second']]
    from src.i18n import saved_text
    from src.evidence_scope import scope_text as evidence_text, LOUISIANA
    lines = [T('wf.note.title', id=r['id']), '', T('wf.note.disclaimer'), '',
             evidence_text(LOUISIANA, lang), '',
             T('wf.note.observation'), '', observation(ctx), '',
             T('wf.note.region'), '',
             T('wf.note.point', lon=f"{r['representative_longitude']:.6f}", lat=f"{r['representative_latitude']:.6f}"),
             T('wf.note.area', area=n(r['area_km2'], 4), pixels=r['pixels']),
             T('wf.note.why', reason=saved_text(r['selection_reason'], lang)), '- ' + T('release.rank_note'), '',
             T('wf.note.dates'), '',
             T('wf.note.pair', d1=d1, d2=d2, days=ctx['interval_days']) +
             (T('wf.note.spans_gap', days=ctx['gaps'][0]['days']) if ctx['gaps'] else ''),
             T('wf.note.seed', seed=rs['seed']), T('wf.note.products')] + [f"  - `{p}`" for p in ctx['product_ids']] + ['',
             f"## {scope_text(PAIR, lang)}", '',
             T('wf.note.recomputed', d1=d1, d2=d2), '',
             T('wf.note.qv_head'), '|---|---:|',
             T('wf.note.valid_pixels', pixels=s.get('pixels', 0))]
    if s.get('pixels'):
        lines += [T('wf.note.median_dhh', v=n(s['HH']['median'], 2, True)), T('wf.note.median_dhv', v=n(s['HV']['median'], 2, True)),
                  T('wf.note.iqr_dhh', lo=n(s['HH']['p25'], 2, True), hi=n(s['HH']['p75'], 2, True)),
                  T('wf.note.iqr_dhv', lo=n(s['HV']['p25'], 2, True), hi=n(s['HV']['p75'], 2, True))]
    lines += [T('wf.note.scene', hh=n(ctx['scene'][0], 2, True), hv=n(ctx['scene'][1], 2, True)),
              T('wf.note.ring', hh=n(ctx['ring']['ring_dHH_db'], 2, True), hv=n(ctx['ring']['ring_dHV_db'], 2, True)),
              T('wf.note.ring_diff', hh=n(ctx['ring']['candidate_minus_ring_dHH_db'], 2, True), hv=n(ctx['ring']['candidate_minus_ring_dHV_db'], 2, True)), '',
              T('wf.note.pattern_head'), '',
              T('wf.note.raw', title=label_text(rd['raw']['key'], lang=lang), reason=reason_text(rd['raw'], lang)),
              T('wf.note.relative', title=label_text(rd['relative']['key'], lang=lang), reason=reason_text(rd['relative'], lang)),
              T('wf.note.result', title=label_text(rd['key'], lang=lang), tau=n(ctx['dead_zone_db'], 2).rstrip('0').rstrip(',.')), '',
              T('wf.note.alternatives')] + [f"- {t(k, lang=lang)}" for k in rd['alternative_keys']] + ['']
    lines += _evidence_table(ctx, PAIR)
    lines += [f"## {scope_text(BASELINE, lang)}", '', T('wf.note.saved', seed=rs['seed']), '',
              T('wf.note.a', top5=rs['variants_in_top5'], total=rs['settings_variants'], r0=rs['rank_range'][0], r1=rs['rank_range'][1],
                p0=rs['screened_pixels_range'][0], p1=rs['screened_pixels_range'][1]),
              T('wf.note.b', same=rs['variants_same_seed'], total=rs['settings_variants'], i0=n(rs['iou_top5_range'][0]), i1=n(rs['iou_top5_range'][1])),
              T('wf.note.lodo', kept=rs['lodo_removals_still_notable'], total=rs['lodo_removals'])
              + (T('wf.note.lodo_failed', dates=', '.join(rs['lodo_dates_not_notable'])) if rs['lodo_dates_not_notable'] else '')
              + (T('wf.note.lodo_untestable', dates=', '.join(rs['lodo_dates_not_testable'])) if rs['lodo_dates_not_testable'] else '') + '.']
    from src.placebo import note_line
    lines += [note_line(ctx.get('placebo'), lang), '']
    lines += _evidence_table(ctx, BASELINE)
    lines += [f"## {scope_text(CONTEXT, lang)}", '']
    lines += _evidence_table(ctx, CONTEXT)
    question, action = investigation_action(ctx)
    lines += ['', '## ' + T('ux.robustness'), ''] + robustness_summary(ctx)
    lines += ['', '## ' + T('ux.action_title'), '', question, '', action, '', T('ux.action_scope')]
    lines += ['', T('wf.note.questions'), ''] + [f"{i}. {q}" for i, q in enumerate(ctx['open_questions'], 1)] + ['',
              T('wf.note.sources'), '']
    return '\n'.join(lines)
