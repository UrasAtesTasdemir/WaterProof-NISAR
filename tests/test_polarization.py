"""Unit fixtures and actual HH/HV provenance/units/mask regression."""
from tests.masked_logs import expected_digest   # release-time path masking (data/masked_logs.json)
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import rasterio
import xarray as xr
from shapely.geometry import box

from src.polarization import DIRECTORY,GROUP,prepare_polarizations,compare_polarizations,load_polarization
from src.nisar_data import RadarDataError
from src.water_change import power_to_db,pixel_area_km2
from scripts.visualize_nisar import read_subset
from scripts.process_polarization import inspect_layers
from src.navigation import apptest_open


class PolarizationTests(unittest.TestCase):
    def test_reader_selects_real_power_term_explicitly(self):
        ds=xr.Dataset({'HHHH':(('y','x'),np.full((3,3),.1)), 'HVHV':(('y','x'),np.full((3,3),.01)),
            'projection':xr.DataArray(4326,attrs={'epsg_code':4326}),
            'xCoordinates':('x',[.5,1.5,2.5]),'yCoordinates':('y',[2.5,1.5,.5]),
            'xCoordinateSpacing':xr.DataArray(1.),'yCoordinateSpacing':xr.DataArray(-1.)})
        for layer in ('HHHH','HVHV'):ds[layer].attrs['units']='1'
        layers=inspect_layers(ds);self.assertEqual(set(layers),{'HHHH','HVHV'})
        hh,hdb,crs,tr,hm=read_subset(ds,box(0,0,3,3))
        hv,vdb,_,vt,vm=read_subset(ds,box(0,0,3,3),layer_name='HVHV')
        np.testing.assert_allclose(hdb,-10,atol=1e-5);np.testing.assert_allclose(vdb,-20,atol=1e-5)
        self.assertEqual(hm['layer'],'HHHH');self.assertEqual(vm['layer'],'HVHV');self.assertEqual(tr,vt)
        ds['HVHV'][1,1]=0
        hv,_,_,_,_=read_subset(ds,box(0,0,3,3),layer_name='HVHV');self.assertTrue(np.isnan(hv[1,1]))
        with self.assertRaises(RadarDataError):read_subset(ds,box(0,0,3,3),layer_name='HHHV')
        with self.assertRaises(RadarDataError):inspect_layers(ds.drop_vars('HVHV'))
        ds.HVHV.attrs['units']='dB'
        with self.assertRaises(RadarDataError):inspect_layers(ds)

    def test_linear_power_db_ratio_and_joint_invalid_centers(self):
        hh=np.full((2,3,3),4.);hv=np.ones_like(hh)
        hh[0,0,0]=np.nan;hv[0,1,1]=0;hv[1,2,2]=np.inf
        data=prepare_polarizations(hh,hv)
        self.assertTrue(np.isnan(data['HH'][0,1,1]));self.assertTrue(np.isnan(data['HV'][0,0,0]))
        self.assertFalse(data['valid'][1,2,2]);self.assertFalse(data['common'][0,0])
        np.testing.assert_allclose(data['ratio'][data['valid']],4)
        np.testing.assert_allclose(data['ratio_db'][data['valid']],10*np.log10(4))
        np.testing.assert_allclose(data['ratio_db'],power_to_db(data['ratio']),equal_nan=True)
        with self.assertRaises(ValueError):prepare_polarizations(hh,hv[:1])

    def test_separate_change_sign_same_date_and_no_valid_pair(self):
        hh=np.stack([np.ones((3,3)),np.full((3,3),10.)]);hv=np.stack([np.ones((3,3)),np.full((3,3),.1)])
        data=prepare_polarizations(hh,hv);pair=compare_polarizations(data,0,1)
        np.testing.assert_allclose(pair['HH_delta'],10);np.testing.assert_allclose(pair['HV_delta'],-10)
        np.testing.assert_allclose(pair['ratio_delta_db'],20)
        self.assertIsNone(pair['statistics']['spatial_Pearson_r'])
        np.testing.assert_allclose(compare_polarizations(data,0,0)['HH_delta'],0)
        bad=dict(data,valid=np.zeros_like(data['valid']))
        with self.assertRaises(ValueError):compare_polarizations(bad,0,1)

    def test_actual_hvhv_sources_positive_linear_power_and_no_band_mix(self):
        data=load_polarization();report=data['report'];n=len(report['observations'])
        self.assertIn(n,(2,6));self.assertEqual(report['source_layers'],{'HH':GROUP+'/HHHH','HV':GROUP+'/HVHV'})
        with xr.open_dataset(data['directory']/'hh_hv_cube.nc',engine='h5netcdf') as ds:
            self.assertEqual(ds.attrs['HV_source_layer'],GROUP+'/HVHV')
            self.assertEqual(ds.HVHV_linear_power.attrs['units'],'1');self.assertEqual(ds.HV_filtered_db.attrs['units'],'dB')
            hh=ds.HHHH_linear_power.values;hv=ds.HVHV_linear_power.values
            expected=prepare_polarizations(hh,hv)
            for band in ('HH','HV','ratio_db'):
                np.testing.assert_allclose(data[band],expected[band],atol=5e-6,rtol=0,equal_nan=True)
            np.testing.assert_allclose(ds.HH_HV_power_ratio.values,expected['ratio'],rtol=1e-6,equal_nan=True)
        for source,obs in zip(report['sources'],report['observations']):
            self.assertEqual(source['product_id'],obs['product_id']);self.assertEqual(source['acquisition_utc'],obs['acquisition_utc'])
            self.assertEqual(source['layer'],'HVHV');self.assertEqual(source['hdf5_group'],GROUP)
            self.assertEqual(source['power_units'],'1');self.assertIn('HVHV',source['available_layers'])
            path=DIRECTORY/'raw'/f"hvhv_{obs['date']}.tif"
            with rasterio.open(path) as raw:
                self.assertEqual(raw.tags()['source_layer'],GROUP+'/HVHV')
                np.testing.assert_allclose(raw.read(2),power_to_db(raw.read(1)),atol=5e-6,rtol=0,equal_nan=True)

    def test_actual_matching_grid_native_area_and_temporal_statistics(self):
        from src.time_series import load_time_series
        data=load_polarization();hh=load_time_series();self.assertEqual(data['grid'],hh['grid'])
        self.assertGreater(data['grid']['transform'].a,0);self.assertLess(data['grid']['transform'].e,0)
        self.assertAlmostEqual(data['common'].sum()*pixel_area_km2(data['grid']['crs'],data['grid']['transform']),data['report']['common_valid_area_km2'])
        for i,row in enumerate(data['report']['observations']):
            self.assertAlmostEqual(float(np.median(data['HH'][i][data['common']])),row['HH_median_db'],places=5)
            self.assertAlmostEqual(float(np.median(data['HV'][i][data['common']])),row['HV_median_db'],places=5)
            np.testing.assert_allclose(data['HH'][i][data['common']],hh['db'][i][data['common']],atol=4e-6,rtol=0)
        pair=compare_polarizations(data,0,1);saved=data['report']['before_after_statistics']
        self.assertEqual(pair['statistics']['pixels'],saved['pixels'])
        self.assertAlmostEqual(pair['statistics']['median_HV_delta_db'],saved['median_HV_delta_db'],places=5)

    def test_polarization_widget_bands_dates_metrics_and_workspace_return(self):
        from streamlit.testing.v1 import AppTest
        root=DIRECTORY.parents[1];data=load_polarization();n=len(data['HH'])
        with patch('requests.sessions.Session.request',side_effect=AssertionError('Dashboard network disabled')):
            app=AppTest.from_file(str(root/'app.py'),default_timeout=40).run();apptest_open(app,'NISAR study')  # Explore (with "Start here") is the landing page
            self.assertFalse(app.exception);self.assertEqual(app.metric[0].value,'0.0569 km²')
            apptest_open(app,'Polarization Analysis')
            self.assertFalse(app.exception);self.assertEqual(app.selectbox(key='pol_band').value,'HV')
            for band in ('HH','HV','HH/HV power ratio (dB)'):
                app.selectbox(key='pol_band').select(band).run();self.assertFalse(app.exception)
            for first,second in ((0,1),(1,0),(0,n-1),(n-1,n-1)):
                app.selectbox(key='pol_first').select(first).run()
                app.selectbox(key='pol_second').select(second).run()
                self.assertFalse(app.exception);expected=compare_polarizations(data,first,second)['statistics']
                self.assertEqual(app.metric[1].value,f"{expected['median_HH_delta_db']:.3f} dB")
                self.assertEqual(app.metric[2].value,f"{expected['median_HV_delta_db']:.3f} dB")
            self.assertTrue(any('Identical dates' in i.value for i in app.info))
            apptest_open(app,'HH time series (six dates)')
            self.assertFalse(app.exception);self.assertEqual(app.metric[0].value,'6')
            apptest_open(app,'Benchmark Validation (Sentinel-1)')
            self.assertFalse(app.exception);self.assertEqual(len(app.metric),0)
            apptest_open(app,'Polarization Analysis')
            self.assertFalse(app.exception)
            for key in ('pol_first','pol_second'):
                self.assertEqual(app.selectbox(key=key).proto.default,app.selectbox(key=key).value)
            apptest_open(app,'Geographic map (NISAR)')
            self.assertFalse(app.exception);self.assertEqual(app.metric[2].value,'100.0000 km²')
            apptest_open(app,'NISAR study');self.assertEqual(app.metric[0].value,'0.0569 km²')

    def test_missing_polarization_data_recovery(self):
        from streamlit.testing.v1 import AppTest
        with patch('src.polarization_panel.polarization_inputs',side_effect=FileNotFoundError('fixture')):
            app=AppTest.from_file(str(DIRECTORY.parents[1]/'app.py'),default_timeout=30).run()
            apptest_open(app,'Polarization Analysis')
            self.assertFalse(app.exception);self.assertTrue(app.error)
            self.assertIn('No download was attempted',app.error[0].value)

    def test_preexisting_data_and_benchmark_unchanged(self):
        import hashlib
        root=DIRECTORY.parents[1];snapshot=json.loads((DIRECTORY/'preserved_hashes.json').read_text())
        for name,digest in snapshot.items():
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),expected_digest(name,digest),name)


if __name__=='__main__':unittest.main()
