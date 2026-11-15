"""Regression fixtures for confirmed final-audit defects. No NASA downloads."""
from datetime import date
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
from rasterio.transform import Affine
from rasterio.warp import transform

from src.grid_validation import assert_same_grid,metric_grid,metric_ring
from src.explore_requests import catalog_request,analysis_request,accept_result,current_result
from src.explore import place_mask,analyze,louisiana_cube,review_note
from src.water_change import pixel_area_km2
from rasterio.crs import CRS

TR=Affine(10,0,750000,0,-10,3315000)
ROOT=Path(__file__).resolve().parents[1]


def grid(tr=TR,crs='EPSG:32615',shape=(100,100)):
    return dict(crs=crs,transform=tr,shape=shape)


def cube(hh=None,hv=None,tr=TR):
    hh=np.ones((3,100,100)) if hh is None else hh
    hv=hh.copy() if hv is None else hv
    (lon,),(lat,)=transform('EPSG:32615','EPSG:4326',[750505],[3314495])
    return dict(source='live',lat=lat,lon=lon,window_km=1,dates=['2026-06-21','2026-07-03','2026-07-15'],
                times=['2026-06-21T00:00:00Z','2026-07-03T00:00:00Z','2026-07-15T00:00:00Z'],
                product_ids=['TEST1','TEST2','TEST3'],hh_power=hh,hv_power=hv,crs='EPSG:32615',transform=list(tr)[:6])


class StrictGridTests(unittest.TestCase):
    def test_legacy_30m_bug_reproduced_and_rejected(self):
        shifted=Affine(10,0,750000,0,-10,3315030)
        self.assertTrue(np.allclose(tuple(TR)[:6],tuple(shifted)[:6]))
        with self.assertRaises(ValueError):assert_same_grid(grid(),grid(shifted))

    def test_identical_and_serialization_roundoff(self):
        assert_same_grid(grid(),grid())
        assert_same_grid(grid(),grid(Affine(10,0,750000+1e-8,0,-10,3315000)))

    def test_displacements_resolutions_crs_orientation_dimensions(self):
        for g in (grid(Affine(10,0,750005,0,-10,3315000)),grid(Affine(10,0,750010,0,-10,3315000)),
                  grid(Affine(20,0,750000,0,-10,3315000)),grid(crs='EPSG:32616'),
                  grid(Affine(10,0,750000,0,10,3315000)),grid(Affine(10,1,750000,0,-10,3315000)),grid(shape=(99,100))):
            with self.subTest(g=g),self.assertRaises(ValueError):assert_same_grid(grid(),g)
        # Tiny spacing errors accumulate: corner pixel-centre verification catches them.
        with self.assertRaises(ValueError):assert_same_grid(grid(),grid(Affine(10+1e-7,0,750000,0,-10,3315000)))

    def test_live_engine_rejects_shift_before_returning_cube(self):
        from src.live_engine import run_live,parse_product,LiveError
        from contextlib import contextmanager
        import tempfile
        base='NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_{}_{}_P05023_N_F_J_001.h5'
        products=[parse_product('https://example.org/'+base.format(d+'T111906',d+'T111941')) for d in ('20260621','20260703')]
        @contextmanager
        def opener(product,token):yield product,{'range_bytes_read':100}
        def subset(product,polygon,layer_name):
            tr=TR if product['date']=='2026-06-21' else Affine(10,0,750000,0,-10,3315030)
            return np.ones((100,100)),None,'EPSG:32615',tr,{}
        with tempfile.TemporaryDirectory() as tmp,self.assertRaises(LiveError) as caught:
            run_live(products,29.9,-90.3,1,'TEST',opener=opener,subset=subset,cache_dir=tmp)
        self.assertEqual(caught.exception.key,'live.err.grid')


class CoverageAndUnitsTests(unittest.TestCase):
    def test_fixed_common_masks_remove_false_temporal_shift(self):
        hh=np.ones((3,100,100));hh[:,:,50:]=100;hh[1,:,70:]=np.nan
        result=analyze(cube(hh))
        med=[r['HH_window_median_db'] for r in result['series']]
        self.assertTrue(np.allclose(med,med[0]))
        self.assertNotEqual(result['series'][0]['valid_pixels_this_date'],result['series'][1]['valid_pixels_this_date'])
        self.assertEqual(result['common_pixels'],7000)
        self.assertAlmostEqual(result['common_area_km2'],.7)
        self.assertEqual(result['summary']['HH']['median'],0)
        self.assertIn('Fixed all-date common footprint',review_note(result))

    def test_identical_coverage_and_known_db(self):
        hh=np.ones((3,100,100));hh[1]*=10;hh[2]*=100
        result=analyze(cube(hh))
        self.assertTrue(np.allclose([r['HH_window_median_db'] for r in result['series']],[0,10,20]))
        self.assertAlmostEqual(result['summary']['HH']['median'],20)

    def test_empty_partial_all_invalid_and_nodata_point(self):
        for kind in ('empty','all-invalid','point','tiny'):
            hh=np.ones((3,100,100))
            if kind=='empty':hh[0,:,:50]=np.nan;hh[1,:,50:]=np.nan
            elif kind=='all-invalid':hh[1]=np.nan
            elif kind=='point':hh[:,50,50]=np.nan
            else:hh[:]=np.nan;hh[:,50,50]=1
            with self.subTest(kind=kind),self.assertRaises(ValueError):analyze(cube(hh))

    def test_point_outside_and_boundary_never_substitute(self):
        with self.assertRaises(ValueError):place_mask((100,100),TR,'EPSG:32615',29.9,-90.4)
        for x,y,valid in ((750000.001,3314999.999,True),(751000.001,3314999.999,False),(750500,3314000.001,True)):
            (lon,),(lat,)=transform('EPSG:32615','EPSG:4326',[x],[y])
            if valid:self.assertTrue(place_mask((100,100),TR,'EPSG:32615',lat,lon)[1])
            else:
                with self.assertRaises(ValueError):place_mask((100,100),TR,'EPSG:32615',lat,lon)

    def test_rectangular_metric_area_place_and_ring(self):
        for dy in (10,20):
            tr=Affine(10,0,750000,0,-dy,3315000)
            (lon,),(lat,)=transform('EPSG:32615','EPSG:4326',[750505],[3315000-dy*50.5])
            mask,_=place_mask((150,150),tr,'EPSG:32615',lat,lon)
            self.assertEqual(mask.sum(),250000/(10*dy))
            self.assertAlmostEqual(pixel_area_km2(CRS.from_epsg(32615),tr)*mask.sum(),.25)
            centre=np.zeros((100,100),bool);centre[50,50]=True
            ring=metric_ring(centre,np.ones_like(centre),tr,'EPSG:32615')
            self.assertFalse(ring[50,55]);self.assertTrue(ring[50,56])
            if dy==20:self.assertTrue(ring[53,50]);self.assertFalse(ring[58,50])
        with self.assertRaises(ValueError):metric_grid('EPSG:4326',TR,(100,100))

    def test_real_cached_cube_keeps_provenance_and_common_statistics(self):
        c=louisiana_cube();r=analyze(c)
        self.assertEqual(len(r['dates']),6);self.assertEqual(len(r['cube']['product_ids']),6)
        for i,row in enumerate(r['series']):
            self.assertAlmostEqual(row['HH_place_median_db'],np.median(r['data']['HH'][i][r['place'] & r['common']]))
        self.assertIn(f"{c['lat']:.6f}",review_note(r))


class RequestTests(unittest.TestCase):
    def test_catalog_filters_coordinates_dates_and_analysis_dimensions(self):
        dates=('2026-06-01','2026-09-30');a=catalog_request(29,-90,dates)
        self.assertNotEqual(a,catalog_request(30,-90,dates))
        self.assertNotEqual(a,catalog_request(29,-90,('2026-07-01','2026-09-30')))
        p=[{'product_id':'A'},{'product_id':'B'}];b=analysis_request(p,29,-90,5)
        for kw in (dict(km=10),dict(lat=30),dict(products=[{'product_id':'A'}]),dict(polarizations=('HHHH',)),dict(filter_size=5)):
            args=dict(products=p,lat=29,lon=-90,km=5);args.update(kw)
            self.assertNotEqual(b,analysis_request(**args))
        self.assertEqual(b,analysis_request(p[::-1],29,-90,5))

    def test_stale_and_out_of_order_results_and_return_to_same_request(self):
        state={'result_active':'new'}
        self.assertFalse(accept_result(state,'result','old',{'value':1}))
        self.assertTrue(accept_result(state,'result','new',{'value':2}))
        self.assertIsNone(current_result(state,'result','old'))
        self.assertEqual(current_result(state,'result','new'),{'value':2})
        state['result_active']='other'
        self.assertFalse(accept_result(state,'result','new',{'value':3}))
        state['result_active']='new'
        self.assertEqual(current_result(state,'result','new'),{'value':2})

    def test_precise_map_and_actual_footprint(self):
        from src.precise_selection import selection_map,common_footprint
        from shapely.geometry import shape,Point
        c=cube();footprint=common_footprint(c)
        self.assertTrue(shape(footprint).covers(Point(c['lon'],c['lat'])))
        html=selection_map(c['lat'],c['lon'],1,footprint=footprint)
        self.assertIn('nisar:point',html);self.assertIn('L.control.layers',html)
        self.assertIn('Actual all-date common valid footprint',html)

    def test_ui_stale_catalog_dates_and_window_and_cached_mode(self):
        from streamlit.testing.v1 import AppTest
        from src.navigation import apptest_open
        from src.live_engine import parse_product
        rows=json.loads((ROOT/'data/time_series/manifest.json').read_text())['observations']
        products=[parse_product(r['download_url']) for r in rows]
        with patch('requests.sessions.Session.request',side_effect=AssertionError('No network')),\
             patch('src.explore_panel.search_catalog',return_value=(products,False)),\
             patch('src.explore_panel.server_token',return_value=None):
            app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run();apptest_open(app,'Explore the world')
            self.assertFalse(app.exception)
            self.assertTrue(app.date_input(key='ex_dates').disabled)
            self.assertTrue(app.slider(key='ex_window').disabled)
            app.selectbox(key='ex_preset').select('custom').run()
            app.button(key='ex_catalog_search').click().run()
            self.assertFalse(app.exception)
            old=app.session_state['ex_catalog']['request_id']
            app.date_input(key='ex_dates').set_value((date(2026,7,1),date(2026,9,30))).run()
            self.assertNotEqual(old,app.session_state['ex_catalog_active'])
            self.assertTrue(any('hidden' in i.value for i in app.info))
            self.assertFalse(app.exception)
            app.button(key='ex_catalog_search').click().run()
            cat=app.session_state['ex_catalog_active']
            app.slider(key='ex_window').set_value(10).run()
            self.assertEqual(cat,app.session_state['ex_catalog_active']) # window does not change point catalog
            self.assertFalse(app.exception)
            # A loaded result for the former window must not render for a new extent/products.
            selected=products[-6:]
            rid=analysis_request(selected,app.session_state['ex_lat'],app.session_state['ex_lon'],10)
            from src.explore import louisiana_cube
            stored=louisiana_cube();stored['source']='live'
            app.session_state['ex_cube']={'request_id':rid,'payload':stored}
            app.slider(key='ex_window').set_value(5).run()
            self.assertTrue(any('hidden' in i.value for i in app.info))
            self.assertFalse(app.exception)
            pick=next(w for w in app.multiselect if w.key.startswith('ex_dates_pick_'))
            pick.set_value(pick.value[:2]).run()
            self.assertTrue(any('hidden' in i.value for i in app.info))
            self.assertFalse(app.exception)


if __name__=='__main__':unittest.main()
