"""Explainable geographic investigation priorities, never flood/risk inference."""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import label,find_objects
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape,mapping
from shapely.ops import unary_union
from src.water_change import pixel_area_km2

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'data/investigation_engine'
DEFAULTS={'magnitude_floor_db':3.,'scene_percentile':90.,'minimum_pixels':25,'connectivity':4,
          'maximum_regions':5,'minimum_centroid_separation_m':100.,'linear_filter_size':3}
LIMITATIONS=[
    'Investigation candidates only; NOT confirmed floods, risk predictions or environmental damage assessments.',
    'Ranking is a descriptive heuristic, not confidence, probability, accuracy or ecological importance.',
    'The same observations select and describe candidates; extreme values and percentile-tail selection are not independent validation.',
    'Six irregular dates cannot establish continuous persistence or capture every short-lived event.',
    'Notable adjacent intervals are not independent recurring events; one anomalous date can create both a rise and a fall.',
    'Screening favors abrupt localized changes and can miss gradual, scene-wide or smaller-footprint changes; an unselected area is not verified stable.',
    'HH drives spatial screening. HV is descriptive; its calibrated noise floor remains unresolved because available noise metadata are DN^2.',
    'Speckle, smoothing, mixed pixels, moisture, vegetation, wind, drainage/tides, registration and provisional processing can influence scattering.',
    'Phase4 found strong threshold/filter sensitivity and regional darkening differences; no scene-median normalization is applied.',
    'Finite-positive common masks cover all six dates; detailed GCOV quality windows were inspected only for the original pair.',
    'Sentinel-1 benchmark scores do not establish NISAR HH/HV accuracy. Independent date-matched validation remains unavailable.'
]


def event_components(hh,common,floor_db=3.,percentile=90.,minimum_pixels=25):
    """Same-date/sign 4-connected tails. No gap filling, dilation or forced regions."""
    hh=np.asarray(hh,dtype=float);common=np.asarray(common,dtype=bool)
    if hh.ndim!=3 or hh.shape[1:]!=common.shape or hh.shape[0]<2:raise ValueError('Expected a time/y/x cube and matching common mask.')
    if not np.isfinite([floor_db,percentile]).all() or floor_db<=0 or not 0<percentile<100 or not isinstance(minimum_pixels,int) or minimum_pixels<1:
        raise ValueError('Invalid descriptive screening settings.')
    common=common&np.isfinite(hh).all(axis=0)
    if not common.any():return [],[],np.zeros(common.shape,dtype=bool)
    proposals=[];scene=[];eligible=np.zeros(common.shape,dtype=bool)
    for i in range(len(hh)-1):
        delta=hh[i+1]-hh[i];values=delta[common];q=float(np.percentile(np.abs(values),percentile))
        scene.append(dict(interval=i,median_HH_delta_db=float(np.median(values)),absolute_change_percentile_db=q,
                          magnitude_floor_db=float(floor_db),effective_cut_db=max(float(floor_db),q)))
        notable=common&(np.abs(delta)>=floor_db)&(np.abs(delta)>q)
        for direction in (-1,1):
            components,count=label(notable&(delta*direction>0),structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
            for component,sl in enumerate(find_objects(components),1):
                if sl is None:continue
                local=components[sl]==component;pixels=int(local.sum())
                if pixels<minimum_pixels:continue
                rr,cc=np.nonzero(local);rr+=sl[0].start;cc+=sl[1].start
                indices=np.ravel_multi_index((rr,cc),common.shape)
                eligible[rr,cc]=True
                proposals.append(dict(indices=indices,seed_interval=i,seed_direction=direction,pixels=pixels,
                    row_mean=float(rr.mean()),column_mean=float(cc.mean()),first_flat_index=int(indices.min())))
    return proposals,scene,eligible


def describe_proposals(proposals,hh,hv,scene):
    """All features on each fixed footprint; medians of pixel differences explicit."""
    if np.shape(hh)!=np.shape(hv):raise ValueError('HH/HV descriptive cubes must match.')
    h=np.asarray(hh).reshape(len(hh),-1);v=np.asarray(hv).reshape(len(hv),-1)
    for p in proposals:
        values=h[:,p['indices']];other=v[:,p['indices']]
        if not np.isfinite(values).all() or not np.isfinite(other).all():raise ValueError('Region includes missing HH/HV observations.')
        delta=np.median(np.diff(values,axis=0),axis=1)
        hv_delta=np.median(np.diff(other,axis=0),axis=1)
        notable=[bool(abs(x)>=s['magnitude_floor_db'] and abs(x)>s['absolute_change_percentile_db']) for x,s in zip(delta,scene)]
        p.update(recurrence_count=sum(notable),maximum_absolute_median_HH_change_db=float(np.max(np.abs(delta))),
                 median_HH_interval_changes_db=delta.tolist(),median_HV_interval_changes_db=hv_delta.tolist(),notable_intervals=notable)
    return proposals


def ranking_key(p):
    return (-p['recurrence_count'],-p['pixels'],-p['maximum_absolute_median_HH_change_db'],p['seed_interval'],p['first_flat_index'],p['seed_direction'])


def rank_regions(proposals,pixel_size_m=10.,maximum=5,separation_m=100.):
    """Lexicographic rank; reject overlap or nearby centers without merging data."""
    if not isinstance(maximum,int) or not 0<=maximum<=5 or not np.isfinite([pixel_size_m,separation_m]).all() or pixel_size_m<=0 or separation_m<0:raise ValueError('Invalid region-selection settings.')
    if maximum==0:return []
    selected=[]
    for p in sorted(proposals,key=ranking_key):
        if any(np.intersect1d(p['indices'],s['indices'],assume_unique=True).size or
               np.hypot(p['row_mean']-s['row_mean'],p['column_mean']-s['column_mean'])*pixel_size_m<separation_m for s in selected):continue
        selected.append(p)
        if len(selected)==maximum:break
    return selected


def polygon_for_indices(indices,grid):
    mask=np.zeros(grid['shape'],dtype='uint8');mask.ravel()[indices]=1
    geom=unary_union([shape(g) for g,value in shapes(mask,mask=mask.astype(bool),transform=grid['transform'],connectivity=4) if value==1])
    return geom


def region_record(p,rank,data,scene,sensitivity,diagnostics):
    grid=data['grid'];mask=np.zeros(grid['shape'],bool);mask.ravel()[p['indices']]=True
    from scipy.ndimage import binary_erosion
    touches_boundary=bool(np.any(mask&~binary_erosion(data['common'],structure=np.array([[0,1,0],[1,1,1],[0,1,0]]),border_value=0)))
    geom=polygon_for_indices(p['indices'],grid);point=geom.representative_point()
    # Densify on the actual 10m grid before changing CRS. Long projected straight
    # edges otherwise become geographic chords with tiny inconsistent slivers.
    geo=transform_geom(grid['crs'],'EPSG:4326',mapping(geom.segmentize(10)));geopoint=transform_geom(grid['crs'],'EPSG:4326',mapping(point))
    observations=data['report']['observations'];times=[];intervals=[]
    for i,o in enumerate(observations):
        row={'date':o['date'],'acquisition_utc':o['acquisition_utc'],'product_id':o['product_id'],'valid_pixels':p['pixels']}
        for band in ('HH','HV'):
            q=np.percentile(data[band][i][mask],[25,50,75]);row.update({band+'_p25_db':float(q[0]),band+'_median_db':float(q[1]),band+'_p75_db':float(q[2])})
        times.append(row)
    for i,s in enumerate(scene):
        intervals.append(dict(selected_date=observations[i]['date'],comparison_date=observations[i+1]['date'],
            median_HH_delta_db=p['median_HH_interval_changes_db'][i],median_HV_delta_db=p['median_HV_interval_changes_db'][i],
            scene_median_HH_delta_db=s['median_HH_delta_db'],scene_abs_percentile_db=s['absolute_change_percentile_db'],effective_cut_db=s['effective_cut_db'],
            region_notable=p['notable_intervals'][i]))
    seed=p['seed_interval'];departures=[];longest=run=0
    for i in range(seed+1,len(observations)):
        value=float(np.median((data['HH'][i]-data['HH'][seed])[mask]));shifted=p['seed_direction']*value>=DEFAULTS['magnitude_floor_db']
        run=run+1 if shifted else 0;longest=max(longest,run)
        departures.append(dict(date=observations[i]['date'],median_HH_departure_from_seed_before_db=value,same_direction_departure_at_least3db=bool(shifted)))
    peak=max((i for i,n in enumerate(p['notable_intervals']) if n),key=lambda i:abs(p['median_HH_interval_changes_db'][i]))
    quality_support=diagnostics['score_gate'][mask]
    return dict(id=rank,pixels=p['pixels'],area_km2=p['pixels']*pixel_area_km2(grid['crs'],grid['transform']),
        representative_longitude=float(geopoint['coordinates'][0]),representative_latitude=float(geopoint['coordinates'][1]),geometry=geo,
        native_bounds_m=list(geom.bounds),touches_processed_boundary=touches_boundary,seed_interval=seed,seed_direction='increase' if p['seed_direction']>0 else 'decrease',
        recurrence_count=p['recurrence_count'],maximum_absolute_median_HH_change_db=p['maximum_absolute_median_HH_change_db'],
        HH_median_pixel_temporal_range_db=float(np.median(np.ptp(data['HH'][:,mask],axis=0))),
        HV_median_pixel_temporal_range_db=float(np.median(np.ptp(data['HV'][:,mask],axis=0))),
        notable_intervals=intervals,temporal_statistics=times,post_seed_departures=departures,longest_run_of_observed_shifted_dates=int(longest),
        sensitivity=sensitivity,original_pair_temporal_scaled_gate_support_pixels=int(np.count_nonzero(quality_support)),
        selection_reason=f"{p['recurrence_count']}/5 region-median intervals exceed both the 3 dB floor and their scene absolute-change 90th percentile; {p['pixels']} same-interval/direction 4-connected cells. Rank then favors area and magnitude, not environmental risk."+(' This component touches the processed boundary; its area is clipped to the cached footprint and does not establish the full feature extent.' if touches_boundary else ''),
        observed_HH_HV_pattern=f"Largest median HH interval: {observations[peak]['date']} to {observations[peak+1]['date']}; HH {p['median_HH_interval_changes_db'][peak]:+.3f} dB, HV {p['median_HV_interval_changes_db'][peak]:+.3f} dB. Different channel responses do not identify a physical cause.",
        possible_interpretations='Changing surface/canopy moisture, vegetation structure, open-water roughness/wind, drainage/tides, geometry, processing or residual speckle are competing hypotheses; none is established.',
        suggested_next_step=f"Obtain an independent date-matched optical/water reference over this exact polygon for {observations[peak]['date']}–{observations[peak+1]['date']}; if unavailable, document the gap and request local observations before attributing a cause.")


def markdown_report(region,manifest):
    """A self-contained non-sensitive report, entirely from saved real summaries."""
    r=region;lines=[f"# WaterProof — Investigation region {r['id']}",
        '', '**Investigation candidate only. NOT confirmed flooding, environmental damage, flood risk or calibrated confidence.**','',
        f"Representative WGS84 point: {r['representative_longitude']:.6f}, {r['representative_latitude']:.6f} (longitude, latitude).",
        f"Approximate native-grid area: {r['area_km2']:.4f} km² ({r['pixels']} cells; EPSG:32615, 10 m pixel spacing).",'',
        '## Why investigate','',r['selection_reason'],'',r['observed_HH_HV_pattern'],'',
        f"Longest run of observed same-direction ≥3dB departures after the seed event: {r['longest_run_of_observed_shifted_dates']} sampled dates. Sparse observations do not establish continuous persistence.",
        '',f"Median pixel-wise six-date range: HH {r['HH_median_pixel_temporal_range_db']:.3f} dB; HV {r['HV_median_pixel_temporal_range_db']:.3f} dB.",
        '', '## Actual temporal observations','', '| Acquisition UTC | HH median dB | HV median dB | Valid cells |','|---|---:|---:|---:|']
    for t in r['temporal_statistics']:lines.append(f"| {t['acquisition_utc']} | {t['HH_median_db']:.4f} | {t['HV_median_db']:.4f} | {t['valid_pixels']} |")
    lines+=['','## Consecutive interval statistics','', '| Dates | Median pixel ΔHH dB | Median pixel ΔHV dB | Scene median ΔHH dB | Notable |','|---|---:|---:|---:|---|']
    for t in r['notable_intervals']:lines.append(f"| {t['selected_date']} → {t['comparison_date']} | {t['median_HH_delta_db']:.4f} | {t['median_HV_delta_db']:.4f} | {t['scene_median_HH_delta_db']:.4f} | {t['region_notable']} |")
    lines+=['','Medians of pixel differences need not equal differences of region medians. No scene median is subtracted.','',
        '## Sensitivity of this fixed footprint','', '| Linear filter side | Magnitude floor dB | Cells still screened in any interval | Original cells |','|---|---:|---:|---:|']
    for s in r['sensitivity']:lines.append(f"| {s['filter_size']} | {s['magnitude_floor_db']} | {s['retained_pixels']} | {r['pixels']} |")
    lines+=['','Retention is setting sensitivity, not confidence; candidates are not reranked to maximize a result.','',
        '## Criteria and provenance','', '```json',json.dumps(manifest['settings'],indent=2),'```',
        '', 'Ranking: recurrence count descending; area descending; maximum absolute region-median HH change descending; deterministic date/location tie-break. Overlap or centers within100 m are suppressed; no merging/dilation is applied.',
        '', 'HH source: /science/LSAR/GCOV/grids/frequencyA/HHHH', 'HV source: /science/LSAR/GCOV/grids/frequencyA/HVHV',
        'Matched finite-positive all-six-date mask; 3×3 normalized linear-power mean before 10 log10; dB data are not converted twice.','']
    for t in r['temporal_statistics']:lines.append(f"- {t['acquisition_utc']}: `{t['product_id']}`")
    lines+=['','## Interpretations, uncertainty and next step','',r['possible_interpretations'],'']
    lines += ['- '+s for s in LIMITATIONS]
    lines+=['',r['suggested_next_step'],'']
    return '\n'.join(lines)


def load_investigations(directory=DIRECTORY):
    directory=Path(directory);report=json.loads((directory/'results.json').read_text())
    if report['status'] not in ('success','no_candidates') or not 0<=len(report['regions'])<=5:raise ValueError('Invalid investigation output.')
    if report['crs']!='EPSG:32615' or len(report['observations'])!=6:raise ValueError('Expected the existing six-date Louisiana study.')
    import hashlib
    for name,digest in report['source_fingerprints'].items():
        path=ROOT/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Cached investigation source fingerprint changed.')
    for index,r in enumerate(report['regions'],1):
        if r['id']!=index or r['pixels']<report['settings']['minimum_pixels'] or len(r['temporal_statistics'])!=6:raise ValueError('Inconsistent region summary.')
        if not np.isclose(r['area_km2'],r['pixels']*.0001):raise ValueError('Native projected region area mismatch.')
        geom=shape(r['geometry'])
        from shapely.geometry import Point
        if not geom.is_valid or not geom.contains(Point(r['representative_longitude'],r['representative_latitude'])):raise ValueError('Invalid investigation geometry or representative point.')
        if [t['product_id'] for t in r['temporal_statistics']]!=[o['product_id'] for o in report['observations']]:raise ValueError('Investigation dates/IDs differ from their real sources.')
    return report
