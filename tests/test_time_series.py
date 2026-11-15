"""Scientific fixtures plus read-only checks on the real six-date cube."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import rasterio
import xarray as xr
from rasterio.transform import xy
from rasterio.warp import transform

from src.time_series import DATES, DIRECTORY, load_time_series, temporal_summary, pair_difference, point_series
from src.water_change import mask_aware_mean, power_to_db, pixel_area_km2
from scripts.process_time_series import verify_catalog
from src.time_series_map import continuous_display, build_time_map
from src.navigation import apptest_open


class TimeSeriesTests(unittest.TestCase):
    def test_temporal_residual_zero_variance_outlier_missing(self):
        a = np.full((6, 2, 3), -15.)
        a[-1, 0, 0] = 30.
        a[:, 0, 1] = np.nan
        a[:3, 1, 1] = np.nan
        median, anomaly, count = temporal_summary(a)
        self.assertEqual(median[0, 0], -15)
        self.assertEqual(anomaly[-1, 0, 0], 45)
        self.assertEqual(anomaly[0, 1, 0], 0)
        self.assertTrue(np.isnan(median[0, 1]))
        self.assertTrue(np.isnan(anomaly[:, 1, 1]).all())
        self.assertEqual(count[1, 1], 3)
        self.assertFalse(np.isinf(anomaly).any())
        with self.assertRaises(ValueError): temporal_summary(np.ones((2, 2, 2)))

    def test_pair_sign_common_mask_and_identical_dates(self):
        a = np.array([[[-20., np.nan]], [[-14., -13.]]])
        delta, valid = pair_difference(a, 0, 1)
        self.assertEqual(delta[0, 0], 6)
        self.assertFalse(valid[0, 1]); self.assertTrue(np.isnan(delta[0, 1]))
        np.testing.assert_allclose(pair_difference(a, 1, 0)[0], -delta, equal_nan=True)
        np.testing.assert_allclose(pair_difference(a, 1, 1)[0], 0)
        with self.assertRaises(ValueError): pair_difference(a, 0, 8)

    def test_real_six_date_grid_units_masks_and_geolocation(self):
        data = load_time_series()
        report = data['report']; db = data['db']; grid = data['grid']
        self.assertEqual(db.shape[0], 6); self.assertTrue(grid['crs'].is_projected)
        self.assertGreater(grid['transform'].a, 0); self.assertLess(grid['transform'].e, 0)
        self.assertEqual([o['date'] for o in report['observations']], list(DATES))
        self.assertAlmostEqual(data['common'].sum()*pixel_area_km2(grid['crs'], grid['transform']), report['common_valid_area_km2'])
        self.assertGreater(report['common_fraction_of_original_valid'], .8)
        with xr.open_dataset(DIRECTORY/'hh_time_series.nc', engine='h5netcdf') as ds:
            self.assertEqual(ds.HHHH_linear_power.attrs['units'], '1')
            self.assertEqual(ds.HH_filtered_db.attrs['units'], 'dB')
            self.assertIn('/frequencyA/HHHH', ds.attrs['source_layer'])
            self.assertFalse(any('HV' in name for name in ds.data_vars))
            np.testing.assert_allclose(ds.x.values, grid['transform'].c+(np.arange(db.shape[2])+.5)*10)
            np.testing.assert_allclose(ds.y.values, grid['transform'].f-(np.arange(db.shape[1])+.5)*10)
            power = ds.HHHH_linear_power.values
            for i in range(6):
                valid = np.isfinite(power[i]) & (power[i] > 0)
                expected = power_to_db(mask_aware_mean(power[i], valid, 3))
                np.testing.assert_allclose(db[i], expected, atol=4e-6, rtol=0, equal_nan=True)
            common = ds.HH_common_db.values
            self.assertTrue(np.isnan(common[:, ~data['common']]).all())
            median, anomaly, _ = temporal_summary(common)
            np.testing.assert_allclose(ds.temporal_median_db.values, median, atol=4e-6, rtol=0, equal_nan=True)
            np.testing.assert_allclose(ds.exploratory_anomaly_db.values, anomaly, atol=5e-6, rtol=0, equal_nan=True)
            for time, item in zip(ds.time.values, report['observations']):
                self.assertEqual(time, np.datetime64(item['acquisition_utc'].replace('+00:00','').replace('Z',''),'ns'))

    def test_real_selected_point_matches_native_pixel_and_missing(self):
        data = load_time_series(); grid = data['grid']
        row, col = np.argwhere(data['common'])[len(np.argwhere(data['common']))//2]
        east, north = xy(grid['transform'], int(row), int(col))
        lon, lat = transform(grid['crs'], 'EPSG:4326', [east], [north])
        point = point_series(data, lon[0], lat[0])
        self.assertEqual((point['row'], point['column']), (row, col))
        np.testing.assert_allclose([r['HH backscatter (dB)'] for r in point['rows']], data['db'][:,row,col])
        self.assertTrue(all(r['Valid neighborhood pixels'] == 1 for r in point['rows']))
        damaged = dict(data, db=data['db'].copy()); damaged['db'][2,row,col] = np.nan
        missing = point_series(damaged, lon[0], lat[0])['rows'][2]
        self.assertIsNone(missing['HH backscatter (dB)']); self.assertEqual(missing['Status'], 'missing / no data')
        neighborhood = point_series(data, lon[0], lat[0], 1)
        self.assertAlmostEqual(neighborhood['rows'][0]['HH backscatter (dB)'], float(np.nanmedian(data['db'][0,row-1:row+2,col-1:col+2])))
        with self.assertRaises(ValueError): point_series(data, -100, 40)

    def test_catalog_configuration_and_reject_incompatible_or_uncovered(self):
        from shapely import wkt
        root = DIRECTORY.parents[1]
        catalog = json.loads((DIRECTORY/'catalog.geojson').read_text())
        inventory = json.loads((root/'data/pair_selection/nisar_inventory.json').read_text())
        manifest = json.loads((DIRECTORY/'manifest.json').read_text())
        selected = verify_catalog(catalog, inventory, wkt.loads(manifest['aoi_wkt']))
        self.assertEqual(len(selected), 6)
        self.assertEqual({p['filename_fields']['track'] for p in selected}, {'105'})
        self.assertEqual({p['filename_fields']['frame'] for p in selected}, {'017'})
        wrong = json.loads(json.dumps(catalog))
        target = next(f for f in wrong['features'] if f['properties']['fileID'] == selected[0]['product_id'])
        target['properties']['frameNumber'] = 999
        with self.assertRaises(ValueError): verify_catalog(wrong, inventory, wkt.loads(manifest['aoi_wkt']))
        with self.assertRaises(ValueError): verify_catalog(catalog, inventory, wkt.loads('POLYGON((-96 29,-95.9 29,-95.9 29.1,-96 29.1,-96 29))'))

    def test_continuous_map_orientation_transparency_and_real_layers(self):
        from rasterio.transform import Affine
        values = np.full((4,4), -10.); values[0,0] = -20; values[3,3] = 0; values[1,1] = np.nan
        grid = dict(crs='EPSG:3857',transform=Affine(10,0,0,0,-10,40),shape=(4,4))
        rgba, bounds = continuous_display(values,grid,-20,0,max_pixels=4)
        self.assertEqual(rgba[0,0,0],0); self.assertEqual(rgba[3,3,0],255)
        self.assertEqual(rgba[1,1,3],0); self.assertEqual(rgba[0,0,3],205)
        self.assertGreater(bounds[1][0],bounds[0][0]); self.assertGreater(bounds[1][1],bounds[0][1])
        data = load_time_series()
        for layer in ('Selected observation','Comparison observation','Comparison − selected (dB)','Selected anomaly (dB)'):
            markup = build_time_map(data,0,5,layer)
            self.assertIn('imageOverlay',markup); self.assertIn('OpenStreetMap',markup)
            self.assertIn('Six-date common valid footprint',markup); self.assertIn('not confirmed flooding',markup)
            self.assertLess(len(markup),2*1024*1024)

    def test_time_series_widgets_real_dates_point_and_preserved_workspaces(self):
        from streamlit.testing.v1 import AppTest
        root = DIRECTORY.parents[1]
        with patch('requests.sessions.Session.request',side_effect=AssertionError('Dashboard network disabled')):
            app = AppTest.from_file(str(root/'app.py'),default_timeout=30).run();apptest_open(app,'NISAR study')  # Explore (with "Start here") is the landing page
            self.assertFalse(app.exception); self.assertEqual(app.metric[0].value,'0.0569 km²')
            apptest_open(app,'HH time series (six dates)')
            self.assertFalse(app.exception)
            self.assertEqual(app.metric[0].value,'6')
            self.assertEqual(app.metric[1].value,'13.8779 km²')
            for i in range(6):
                app.selectbox(key='ts_first').select(i).run()
                self.assertFalse(app.exception)
                self.assertTrue(any(DATES[i] in c.value and 'comparison' in c.value for c in app.caption))
            app.selectbox(key='ts_second').select(5).run()
            app.selectbox(key='ts_layer').select('Comparison − selected (dB)').run()
            self.assertTrue(any('exactly zero' in x.value for x in app.info))
            data = load_time_series(); indices = np.argwhere(data['common']); row,col = indices[len(indices)//3]
            east,north = xy(data['grid']['transform'],int(row),int(col))
            lon,lat = transform(data['grid']['crs'],'EPSG:4326',[east],[north])
            app.number_input(key='ts_lon').set_value(lon[0]); app.number_input(key='ts_lat').set_value(lat[0])
            next(b for b in app.button if b.label=='Apply point').click().run()
            self.assertFalse(app.exception)
            table = app.table[0].value
            np.testing.assert_allclose(table['HH backscatter (dB)'].values,data['db'][:,row,col])
            self.assertEqual(table['Valid neighborhood pixels'].tolist(),[1]*6)
            app.number_input(key='ts_lon').set_value(-100.)
            next(b for b in app.button if b.label=='Apply point').click().run()
            self.assertFalse(app.exception); self.assertTrue(any('outside the cached raster' in x.value for x in app.error))
            apptest_open(app,'Geographic map (NISAR)')
            self.assertFalse(app.exception); self.assertEqual(app.metric[2].value,'100.0000 km²')
            apptest_open(app,'Benchmark Validation (Sentinel-1)')
            self.assertFalse(app.exception); self.assertEqual(len(app.metric),0)
            apptest_open(app,'HH time series (six dates)')
            self.assertFalse(app.exception)
            # Browser protobuf defaults must match the server's retained values.
            for key in ('ts_first','ts_second','ts_radius'):
                widget = app.selectbox(key=key)
                self.assertEqual(widget.proto.default,widget.value)
            for key in ('ts_lon','ts_lat'):
                widget = app.number_input(key=key)
                self.assertAlmostEqual(widget.proto.default,widget.value)
            apptest_open(app,'NISAR study')
            self.assertEqual(app.metric[0].value,'0.0569 km²')

    def test_time_series_missing_files_recovery(self):
        from streamlit.testing.v1 import AppTest
        with patch('src.time_series_panel.file_signature',side_effect=FileNotFoundError('fixture')):
            app = AppTest.from_file(str(DIRECTORY.parents[1]/'app.py'),default_timeout=30).run()
            apptest_open(app,'HH time series (six dates)')
            self.assertFalse(app.exception); self.assertTrue(app.error)
            self.assertIn('No download was attempted',app.error[0].value)


if __name__ == '__main__':
    unittest.main()
