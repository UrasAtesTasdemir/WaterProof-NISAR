"""Geographic/ranking fixtures and verification against actual cached NISAR."""
from tests.masked_logs import expected_digest   # release-time path masking (data/masked_logs.json)
import hashlib,json,unittest
from unittest.mock import patch
import numpy as np
import rasterio
from rasterio.warp import transform_geom
from shapely.geometry import shape,Point
from src.investigation import DIRECTORY,DEFAULTS,event_components,describe_proposals,rank_regions,load_investigations,markdown_report
from src.investigation_panel import investigation_map
from src.polarization import load_polarization
from src.navigation import apptest_open


class InvestigationTests(unittest.TestCase):
    def test_no_candidates_identical_uniform_small_or_invalid(self):
        data=np.full((6,30,30),-10.);valid=np.ones((30,30),bool)
        self.assertEqual(event_components(data,valid)[0],[])
        data[1:]-=5;self.assertEqual(event_components(data,valid)[0],[]) # Global uniform change is not a localized tail.
        data=np.full((6,30,30),-10.);data[1:,2,2]-=10
        self.assertEqual(event_components(data,valid)[0],[])
        data[1:,5:10,5:10]-=6;valid[5:10,5:10]=False
        self.assertEqual(event_components(data,valid)[0],[])
        with self.assertRaises(ValueError):event_components(data,valid,floor_db=-1)

    def test_four_connectivity_sign_and_no_missing_HV(self):
        data=np.zeros((6,20,20));data[1:,2:4,2:4]=5;data[1:,4:6,4:6]=5
        proposals,scene,eligible=event_components(data,np.ones((20,20),bool),minimum_pixels=4)
        self.assertEqual(len(proposals),2);self.assertEqual([p['pixels'] for p in proposals],[4,4])
        proposals=describe_proposals(proposals,data,data.copy(),scene);self.assertTrue(all(p['recurrence_count']==1 for p in proposals))
        bad=data.copy();bad[:,2,2]=np.nan
        with self.assertRaises(ValueError):describe_proposals(proposals,data,bad,scene)

    def test_deterministic_lexicographic_ranking_and_overlap_suppression(self):
        def p(start,size,recurrence,magnitude):return dict(indices=np.arange(start,start+size),pixels=size,recurrence_count=recurrence,
            maximum_absolute_median_HH_change_db=magnitude,seed_interval=0,seed_direction=1,first_flat_index=start,row_mean=start,column_mean=0.)
        a=p(0,25,2,10);b=p(100,25,3,4);c=p(200,50,2,5);duplicate=p(100,25,1,30)
        chosen=rank_regions([a,duplicate,c,b],separation_m=0)
        self.assertEqual([x['first_flat_index'] for x in chosen],[100,200,0])
        self.assertEqual([x['first_flat_index'] for x in rank_regions([b,c,a],separation_m=0)], [100,200,0])
        self.assertEqual(rank_regions([a],maximum=0),[])
        with self.assertRaises(ValueError):rank_regions([a],maximum=2.5)
        near=p(500,25,1,3);near['row_mean']=1
        self.assertEqual(len(rank_regions([a,near],separation_m=100)),1)

    def test_real_ranking_matches_actual_cached_observations(self):
        d=load_polarization();r=load_investigations()
        proposals,scene,_=event_components(d['HH'],d['common'])
        selected=rank_regions(describe_proposals(proposals,d['HH'],d['HV'],scene))
        self.assertEqual(len(proposals),r['eligible_proposals']);self.assertEqual(len(selected),len(r['regions']));self.assertLessEqual(len(selected),5)
        with rasterio.open(DIRECTORY/'region_labels.tif') as src:
            labels=src.read(1);self.assertEqual(src.crs,d['grid']['crs']);self.assertEqual(src.transform,d['grid']['transform'])
            from scipy.ndimage import binary_erosion
            boundary=d['common']&~binary_erosion(d['common'],structure=np.array([[0,1,0],[1,1,1],[0,1,0]]),border_value=0)
            self.assertEqual(int(np.isfinite(labels).sum()),r['common_valid_pixels'])
            for rank,p in enumerate(selected,1):
                np.testing.assert_array_equal(np.flatnonzero(labels.ravel()==rank),p['indices'])
                region=r['regions'][rank-1];self.assertEqual(region['recurrence_count'],p['recurrence_count']);self.assertEqual(region['pixels'],p['pixels'])
                mask=labels==rank
                self.assertEqual(region['touches_processed_boundary'],bool((mask&boundary).any()))
                self.assertAlmostEqual(region['HH_median_pixel_temporal_range_db'],float(np.median(np.ptp(d['HH'][:,mask],axis=0))))
                self.assertAlmostEqual(region['HV_median_pixel_temporal_range_db'],float(np.median(np.ptp(d['HV'][:,mask],axis=0))))
                for i,t in enumerate(region['temporal_statistics']):
                    self.assertEqual(t['product_id'],d['report']['observations'][i]['product_id'])
                    self.assertAlmostEqual(t['HH_median_db'],float(np.median(d['HH'][i][mask])))
                    self.assertAlmostEqual(t['HV_median_db'],float(np.median(d['HV'][i][mask])))
                self.assertEqual(next(s for s in region['sensitivity'] if s['filter_size']==3 and s['magnitude_floor_db']==3)['retained_pixels'],region['pixels'])

    def test_actual_geographic_polygons_points_native_areas_and_nonoverlap(self):
        r=load_investigations();footprint=shape(r['common_footprint']);native=[]
        for region in r['regions']:
            geom=shape(region['geometry']);self.assertTrue(geom.contains(Point(region['representative_longitude'],region['representative_latitude'])))
            self.assertLess(region['representative_longitude'],-90.25);self.assertGreater(region['representative_longitude'],-90.32)
            projected=shape(transform_geom('EPSG:4326',r['crs'],region['geometry']));native.append(projected)
            self.assertAlmostEqual(projected.area/1e6,region['area_km2'],places=7)
            self.assertAlmostEqual(projected.area/100,region['pixels'],places=4)
            self.assertLess(geom.difference(footprint.buffer(1e-9)).area,1e-12)
        for i,g in enumerate(native):
            for other in native[:i]:self.assertAlmostEqual(g.intersection(other).area,0,places=5)

    def test_actual_markdown_exports_contain_observations_rules_and_cautions(self):
        r=load_investigations()
        for region in r['regions']:
            text=markdown_report(region,r)
            historical=(DIRECTORY/f"region_{region['id']}_investigation.md").read_text()
            # Only the new export's product heading changes; all historical measurements stay exact.
            self.assertEqual(text,historical.replace('# FloodPulse NISAR —','# WaterProof —',1))
            for o in r['observations']:self.assertIn(o['product_id'],text);self.assertIn(o['acquisition_utc'],text)
            self.assertIn(f"{region['area_km2']:.4f} km²",text)
            self.assertIn('NOT confirmed flooding',text);self.assertIn('not confidence',text);self.assertIn('minimum_pixels',text)
            self.assertNotIn('Authorization: Bearer',text)

    def test_map_numbering_geographic_layers_and_selected_region(self):
        r=load_investigations();html=investigation_map(r,r['regions'][-1]['id'])
        for text in ('OpenStreetMap','Actual six-date processed footprint','NOT risk/confidence','marker','geoJson'):self.assertIn(text,html)
        for region in r['regions']:self.assertIn(f"Region {region['id']}",html)
        self.assertLess(len(html),2*1024*1024)

    def test_widget_region_selection_exports_and_existing_workspaces(self):
        from streamlit.testing.v1 import AppTest
        root=DIRECTORY.parents[1];r=load_investigations()
        with patch('requests.sessions.Session.request',side_effect=AssertionError('Dashboard network disabled')):
            app=AppTest.from_file(str(root/'app.py'),default_timeout=40).run();apptest_open(app,'NISAR study');self.assertEqual(app.metric[0].value,'0.0569 km²')  # Explore (with "Start here") is the landing page
            apptest_open(app,'Investigation Explorer');self.assertFalse(app.exception)
            for region in (r['regions'][0],r['regions'][-1]):
                app.selectbox(key='investigation_region').select(region['id']).run();self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value,f"{region['area_km2']:.4f} km²")
                table=app.table[0].value
                np.testing.assert_allclose(table['HH_median_db'].values,[t['HH_median_db'] for t in region['temporal_statistics']])
                self.assertTrue(app.get('download_button'))
            for workspace in ('Scientific Diagnostics','Polarization Analysis','HH time series (six dates)','Geographic map (NISAR)','Benchmark Validation (Sentinel-1)','Investigation Explorer'):
                apptest_open(app,workspace);self.assertFalse(app.exception)
            widget=app.selectbox(key='investigation_region');self.assertEqual(widget.proto.default,widget.options.index(f'Region {widget.value}'))
            apptest_open(app,'NISAR study');self.assertEqual(app.metric[0].value,'0.0569 km²')

    def test_missing_or_no_candidate_outputs_are_explicit(self):
        from streamlit.testing.v1 import AppTest
        with patch('src.investigation_panel.investigation_signature',side_effect=FileNotFoundError('fixture')):
            app=AppTest.from_file(str(DIRECTORY.parents[1]/'app.py'),default_timeout=30).run()
            apptest_open(app,'Investigation Explorer');self.assertFalse(app.exception)
            self.assertIn('No download or original-result recomputation',app.error[0].value)
        empty={'regions':[],'settings':DEFAULTS}
        with patch('src.investigation_panel.cached_investigations',return_value=empty):
            app=AppTest.from_file(str(DIRECTORY.parents[1]/'app.py'),default_timeout=30).run()
            apptest_open(app,'Investigation Explorer');self.assertFalse(app.exception)
            self.assertTrue(any('No meaningful localized' in i.value for i in app.info))

    def test_existing_scientific_and_benchmark_files_unchanged(self):
        root=DIRECTORY.parents[1]
        for name,digest in json.loads((DIRECTORY/'preserved_hashes.json').read_text()).items():
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),expected_digest(name,digest),name)


if __name__=='__main__':unittest.main()
