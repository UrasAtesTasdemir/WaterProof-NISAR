"""Generate the feasibility decision from actual catalog, subset and gauge records."""
from pathlib import Path
from datetime import datetime
import json,csv,hashlib
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def main():
 ns=json.loads((P/'nisar_inventory.json').read_text());refs=json.loads((P/'reference_windows.json').read_text());hydro=json.loads((P/'hydrologic_timing.json').read_text())
 s1=json.loads((P/'OPERA_L3_DSWX-S1_V1.json').read_text());assert not s1['response']['feed']['entry']
 pairs=[]
 for b in ns:
  for a in ns:
   if b['start_utc'][:10]<'2026-07-16'<a['start_utc'][:10] and 11<=(dt(a['start_utc'])-dt(b['start_utc'])).total_seconds()/86400<=13 and all(a[k]==b[k] for k in ('track','frame','direction','bandwidth','configuration','crid')):
    pairs.append({'before_id':b['product_id'],'after_id':a['product_id'],'track':a['track'],'frame':a['frame'],'nominal_common_aoi_coverage_fraction':min(a['aoi_footprint_coverage_fraction'],b['aoi_footprint_coverage_fraction'])})
 for r in refs:
  if r['status']=='aoi_inspected':assert sum(r['aoi_class_counts'].values())==r['aoi_pixel_centers']
 original=json.loads((ROOT/'data/reliability/results.json').read_text())['preserved_original_hashes']
 for name,digest in original.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
 rows=[]
 for n in ns:
  for r in refs:
   rows.append({'nisar_id':n['product_id'],'reference_id':r['product_id'],'reference_utc':r['acquisition_utc'],'time_offset_hours':r['time_difference_hours'][n['product_id']],'valid_fraction':r.get('valid_fraction'),'status':r['status']})
 with (P/'reference_timing.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary={'decision':'NO-GO for a validated flood-extent demonstration','best_validated_flood_pair':None,'compatible_12day_pairs':pairs,'nisar_observations':ns,'references_inspected':len(refs),'DSWx_S1_hits':0,'gauge_timing':hydro,'interpretation':'Earliest post-event NISAR is 39.6 h after local gauge peak, with stage already far lower; residual inundation cannot be ruled out, but event maximum is not observed. Missing compatible valid post-event references prevents validation. No scenes should be labelled confirmed flood extent. Later dates may show recession or longer-term changes only.','original_files_unchanged':True,'new_geographic_map_built':False,'full_HDF5_downloaded':False}
 (P/'feasibility.json').write_text(json.dumps(summary,indent=2)+'\n')
 text=['# Kerrville data feasibility — NO-GO for validated flood extent','',
'## Research AOI and scope','',
'Exact WGS84 box: −99.18 to −99.10 longitude, 30.01 to 30.09 latitude, centered on Kerrville/Guadalupe and nearby waterways. All research is separate here; Louisiana inputs, pipeline, dashboard and scientific outputs are unchanged. No geographic map or classification for Texas was generated. No full NISAR HDF5 was downloaded.', '',
'ASF GCOV production search: July1 00:00 through August16 00:00 UTC (includes August15). No query reached its result limit. Seven real provisional products were returned. All have frequency-A HH/HV, frequency-B HH/HV, bandwidth4005/DHDH, sourceA, release P05023. Footprint coverage is the catalog geometry intersection with the AOI in EPSG:32614, not a guarantee of valid raster pixels.', '',
'| Acquisition start UTC | Full product ID | Track/frame, direction | Nominal AOI footprint coverage |','|---|---|---|---:|']
 for n in ns:text.append(f"| {n['start_utc']} | `{n['product_id']}` | {n['track']}/{n['frame']} {n['direction']} | {100*min(1,n['aoi_footprint_coverage_fraction']):.2f}% |")
 text+=['','## Timing relative to the event','',
'USGS 08166200 returned an actual stage time series. Within the July14–22 query, the maximum is 30.06 ft on July16 09:50 UTC (provisional P). The earliest subsequent NISAR pass is July18 01:26 UTC, 39.61 hours later; the nearest gauge sample is 4.41 ft, only 1.8 minutes from that pass. July19 NISAR is 74.04 hours after the peak with 2.81 ft at the nearest sample. Stage is local-gauge elevation, not water depth over the floodplain. One station cannot establish flood extent or rule out residual inundation.', '',
'There is no NISAR observation on July16 or July17 in this exact-AOI search. The post-event passes are better interpreted as possible recession/post-event surface observations; they do not measure the event maximum. August12 is a longer-term surface state.', '',
'Compatible pre/post 12-day pairs: July6/18 (track142/frame73, partial AOI), July7/19 (track163/frame17, nominal full AOI), July11/23 (track41/frame73, nominal full AOI). They cannot be combined across tracks as if identical viewing geometry. No scientifically suitable validated flood pair was identified. July6/18 is the earliest technical pair, but only about half of the AOI is covered; July7/19 has better footprint coverage but later recession timing. Neither is recommended as a validated inundation case.', '',
'## Independent reference availability','',
'Exact-AOI CMR searches over July1–August15 returned **zero DSWx-S1 records** and **32 DSWx-HLS records**. Twelve targeted HLS small windows were actually range-read: two nearest sensing-time products around each useful July NISAR date, plus low-tile-cloud July9/20 alternatives. Other late July/August products were not exhaustively sampled; even a clear late reference cannot reconstruct the missed flood peak. Full collection metadata and exact query parameters are saved here.', '',
'All sampled references are 30 m categorical WTR products. Cloud/shadow, snow/ice, ocean and fill are excluded; valid classes are0,1,2. Fractions below use pixel centers inside the exact projected AOI, not tile-wide cloud metadata. Every inspected reference has a timing difference to each NISAR acquisition in reference_timing.csv.', '',
'| Actual reference acquisition UTC | Full product ID | Valid AOI fraction |','|---|---|---:|']
 for r in refs:text.append(f"| {r['acquisition_utc']} | `{r['product_id']}` | {100*r.get('valid_fraction',0):.3f}% |")
 text+=['',
'July7 S2B offers partial valid pre-event coverage (~36.47%). July9 Landsat8 is nearly complete (~99.97%) but is ~53 h after July7 NISAR or ~80 h after July6. July17 windows are entirely cloud/shadow; July18 and July20 are entirely NoData in the AOI. In particular, the July20 catalog tile reports 0% cloud but provides no AOI data: a clear tile attribute is not usable local coverage. July24 sampled coverage is also effectively unusable. There is no verified useful pre/post reference pair for the NISAR event timing. No agreement, flood area or accuracy was computed.', '',
'## Decision','',
'**NO-GO for a scientifically validated flood-extent demonstration using this AOI/date inventory.** Kerrville has a documented flood and a gauge, so event timing is clearer than Louisiana. However, NISAR misses the measured peak and post-event independent references fail local coverage checks. It is not scientifically preferable for the intended validated demonstration. It might support an explicitly unvalidated recession or longer-term change study, which is a different objective.', '',
'No region switch is recommended on the present evidence. Preserve the Louisiana demo with its scientific warnings. Any new case search should require concurrent valid radar and independent-reference windows, rather than selecting a documented event first and assuming usable imagery.', '',
'## Checks and records','',
'All historical Louisiana scientific-file hashes match. Catalog footprints were measured in projected metres. Each reference class count sums to its AOI pixel count, and timing offsets are computed from acquisition timestamps (not processing timestamps). Source datasets retain their full IDs, URLs, product versions and UTC times. The two small NISAR HHHH checks, if complete, are in nisar_small_window_checks.json; these measure raster validity and may differ from approximate catalog footprint coverage.', '',
'Sources: [USGS gauge query](https://waterservices.usgs.gov/nwis/iv/?format=json&sites=08166200&startDT=2026-07-14&endDT=2026-07-22&parameterCd=00065), [City of Kerrville event documentation](https://www.kerrvilletx.gov/2026-Flood-Recovery), [NASA DSWx product](https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-HLS_V1).','']
 (P/'REPORT.md').write_text('\n'.join(text));print('Decision:',summary['decision']);print('Compatible pairs:',len(pairs));print('Original hashes unchanged; reference mask/count/timing checks passed.')
if __name__=='__main__':main()
