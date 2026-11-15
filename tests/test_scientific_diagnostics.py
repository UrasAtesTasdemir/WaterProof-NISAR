"""Robust diagnostic fixtures and actual six-date regression; no test-label tuning."""
from tests.masked_logs import expected_digest   # release-time path masking (data/masked_logs.json)
import hashlib
import json
import unittest
from unittest.mock import patch
import numpy as np
import rasterio
from src.scientific_diagnostics import DIRECTORY,robust_statistics,temporal_scaled_change,local_texture
from src.polarization import load_polarization
from src.water_change import classify,pixel_area_km2
from src.navigation import apptest_open


class ScientificDiagnosticsTests(unittest.TestCase):
    def test_robust_missing_nonfinite_outlier_statistics(self):
        s=robust_statistics([1,2,3,np.nan,np.inf]);self.assertEqual(s['count'],3);self.assertEqual(s['median'],2)
        self.assertAlmostEqual(s['scaled_mad'],1.482602218505602)
        self.assertIsNone(robust_statistics([np.nan,np.inf])['median'])
        self.assertEqual(robust_statistics([1,1,1,10000])['median'],1)

    def test_temporal_scale_leaves_pair_out_zero_variance_and_missing(self):
        a=np.full((6,2,3),-10.);a[1]=a[0]-4
        base=temporal_scaled_change(a);np.testing.assert_allclose(base['scale_db'],1);np.testing.assert_allclose(base['score'],-4)
        a[1]-=30;changed=temporal_scaled_change(a);np.testing.assert_allclose(changed['scale_db'],base['scale_db'])
        a[5,0,0]=10000;self.assertEqual(temporal_scaled_change(a)['scale_db'][0,0],1)
        a[2,1,1]=np.nan;unknown=temporal_scaled_change(a);self.assertFalse(unknown['valid'][1,1]);self.assertTrue(np.isnan(unknown['score'][1,1]))
        a[0,0,1]=np.inf;self.assertTrue(np.isnan(temporal_scaled_change(a)['score'][0,1]))
        with self.assertRaises(ValueError):temporal_scaled_change(a,0,0)
        with self.assertRaises(ValueError):temporal_scaled_change(a,floor_db=0)

    def test_conditional_enl_qualification_only_raw_supported_patches(self):
        rng=np.random.default_rng(1234);p=rng.gamma(4,.25,size=(128,128));looks=np.full(p.shape,5.)
        stats=local_texture(p,looks);self.assertTrue(stats['qualified']);self.assertAlmostEqual(stats['enl'],4,delta=.25)
        self.assertIsNone(local_texture(p,looks,filtered=True)['enl'])
        self.assertIsNone(local_texture(p)['enl'])
        ramp=p*(1+np.arange(128)[None,:]/20);self.assertFalse(local_texture(ramp,looks)['qualified'])
        self.assertIsNone(local_texture(np.full((4,4),np.nan))['enl'])

    def test_real_sources_pairwise_units_area_and_histogram_counts(self):
        r=json.loads((DIRECTORY/'results.json').read_text());d=load_polarization()
        self.assertEqual(len(r['observations']),6);self.assertEqual(len(r['pairwise_distributions']),30)
        self.assertEqual(r['source_layers'],d['report']['source_layers'])
        self.assertAlmostEqual(d['common'].sum()*pixel_area_km2(d['grid']['crs'],d['grid']['transform']),r['common_valid_area_km2'])
        dates=[o['date'] for o in r['observations']]
        for p in r['pairwise_distributions']:
            first=dates.index(p['selected']);second=dates.index(p['comparison'])
            delta=(d[p['band']][second]-d[p['band']][first])[d['common']]
            self.assertEqual(p['count'],len(delta));self.assertAlmostEqual(p['median'],float(np.median(delta)))
            h=p['histogram'];self.assertEqual(sum(h['counts'])+h['below']+h['above'],p['count'])

    def test_real_alternative_subset_score_mask_and_baseline_preserved(self):
        d=load_polarization();r=json.loads((DIRECTORY/'results.json').read_text());scaled=temporal_scaled_change(d['HH'])
        baseline,delta=classify(d['HH'][0],d['HH'][1],d['common'],-16,3)
        self.assertTrue(np.all(np.abs(delta[scaled['gate']])>=3));self.assertTrue(np.all(scaled['scale_db'][scaled['valid']]>=1))
        with rasterio.open(DIRECTORY/'temporal_scaled_change.tif') as src:
            self.assertEqual(src.units,('1','1','dB'))
            np.testing.assert_allclose(src.read(1),scaled['score'],atol=1e-6,rtol=1e-6,equal_nan=True)
            self.assertEqual(src.crs,d['grid']['crs']);self.assertEqual(src.transform,d['grid']['transform'])
        cell=pixel_area_km2(d['grid']['crs'],d['grid']['transform'])
        self.assertAlmostEqual((baseline==2).sum()*cell,.0569);self.assertAlmostEqual((baseline==3).sum()*cell,.0005)
        self.assertLessEqual(r['comparison']['alternative_expansion_km2'],r['comparison']['baseline_expansion_km2'])
        self.assertAlmostEqual(r['comparison']['baseline_expansion_km2'],.0569)
        row=next(s for s in r['sensitivity'] if s['filter_size']==3 and s['water_threshold_db']==-16)
        self.assertEqual(row['expansion_pixels'],569);self.assertEqual(row['recession_pixels'],5)
        with rasterio.open(DIRECTORY/'sensitivity_counts.tif') as src:
            values=src.read(1);self.assertTrue(np.isfinite(values[d['common']]).all());self.assertTrue((values[d['common']]>=0).all());self.assertTrue((values[d['common']]<=12).all())
        families=json.loads((DIRECTORY/'stability_families.json').read_text())['families']
        self.assertEqual([f['expansion_pixels'] for f in families],[63,29])
        for f in families:self.assertAlmostEqual(f['expansion_pixels']*cell,f['expansion_km2'])

    def test_actual_quality_mask_looks_and_noise_units_not_confused(self):
        q=json.loads((DIRECTORY/'quality_metadata.json').read_text());self.assertEqual(q['status'],'success')
        self.assertEqual(len(q['observations']),2)
        for e in q['observations']:
            self.assertEqual(e['layers']['mask']['observed_common_codes'],{'1':138779})
            self.assertTrue(4<e['layers']['numberOfLooks']['median']<6)
            noise=[x for x in e['noise_calibration_inventory'] if x['path'].endswith('/frequencyA/noiseEquivalentBackscatter/HV')]
            self.assertEqual(len(noise),1);self.assertIn('DN^2',noise[0]['attributes']['description'])
        flags=json.loads((DIRECTORY/'processing_flags.json').read_text())
        self.assertEqual(flags['status'],'success');self.assertTrue(all(e['noiseCorrectionApplied']=='False' for e in flags['observations']))

    def test_previous_scientific_data_and_benchmark_fingerprints(self):
        root=DIRECTORY.parents[1]
        for name,digest in json.loads((DIRECTORY/'preserved_hashes.json').read_text()).items():
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),expected_digest(name,digest),name)

    def test_dashboard_diagnostic_controls_and_original_workspaces(self):
        from streamlit.testing.v1 import AppTest
        root=DIRECTORY.parents[1];r=json.loads((DIRECTORY/'results.json').read_text())
        with patch('requests.sessions.Session.request',side_effect=AssertionError('Dashboard network disabled')):
            app=AppTest.from_file(str(root/'app.py'),default_timeout=40).run();apptest_open(app,'NISAR study')  # Explore (with "Start here") is the landing page
            self.assertEqual(app.metric[0].value,'0.0569 km²')
            apptest_open(app,'Scientific Diagnostics');self.assertFalse(app.exception)
            self.assertEqual(app.metric[0].value,'-1.389 dB')
            app.selectbox(key='diag_band').select('HV').run();self.assertFalse(app.exception);self.assertEqual(app.metric[0].value,'-0.720 dB')
            app.selectbox(key='diag_pair').select(14).run();self.assertFalse(app.exception)
            pairs=[p for p in r['pairwise_distributions'] if p['band']=='HV'];self.assertEqual(app.metric[0].value,f"{pairs[14]['median']:.3f} dB")
            app.selectbox(key='diag_quantity').select('recession_km2').run();self.assertFalse(app.exception)
            for workspace in ('Polarization Analysis','HH time series (six dates)','Geographic map (NISAR)','Benchmark Validation (Sentinel-1)','Scientific Diagnostics'):
                apptest_open(app,workspace);self.assertFalse(app.exception)
            self.assertEqual(app.selectbox(key='diag_pair').proto.default,app.selectbox(key='diag_pair').value)
            apptest_open(app,'NISAR study');self.assertEqual(app.metric[0].value,'0.0569 km²')

    def test_missing_diagnostics_graceful_no_network_or_recompute(self):
        from streamlit.testing.v1 import AppTest
        with patch('src.diagnostics_panel.diagnostics_signature',side_effect=FileNotFoundError('fixture')):
            app=AppTest.from_file(str(DIRECTORY.parents[1]/'app.py'),default_timeout=30).run()
            apptest_open(app,'Scientific Diagnostics');self.assertFalse(app.exception)
            self.assertIn('No download or production recomputation',app.error[0].value)


if __name__=='__main__':unittest.main()
