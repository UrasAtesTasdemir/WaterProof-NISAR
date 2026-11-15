"""Projection/orientation/area tests plus real-data dashboard regression."""
from pathlib import Path
import json,unittest
import numpy as np
import rasterio
from rasterio.transform import Affine
from shapely.geometry import shape
from rasterio.warp import transform_geom
from streamlit.testing.v1 import AppTest
from src.geographic_map import visualization_grid,rgba_layer,load_geographic,build_map,ROOT
from src.water_change import mask_aware_mean,power_to_db,classify
from src.navigation import apptest_open

class GeographicMapTests(unittest.TestCase):
 def test_orientation_and_transparency(self):
  a=np.zeros((4,4),dtype='uint8');a[0,0]=2;a[3,3]=3
  display,tr,bounds=visualization_grid(a,'EPSG:3857',Affine(10,0,0,0,-10,40),max_pixels=4)
  np.testing.assert_array_equal(display,a)
  self.assertGreater(bounds[1][0],bounds[0][0]);self.assertGreater(bounds[1][1],bounds[0][1])
  rgba=rgba_layer(display,2);self.assertEqual(rgba[0,0,3],185);self.assertEqual(rgba[3,3,3],0);self.assertEqual(rgba[1,1,3],0)
 def test_actual_louisiana_location_and_native_areas(self):
  for directory in sorted((ROOT/'data/geographic_mapping').glob('*km')):
   if not (directory/'results.json').exists():continue
   meta,display,bounds,fp=load_geographic(directory)
   self.assertLessEqual(max(display.shape),768)
   self.assertLess(bounds[0][0],29.913);self.assertGreater(bounds[1][0],29.913)
   self.assertLess(bounds[0][1],-90.28);self.assertGreater(bounds[1][1],-90.28)
   area=shape(transform_geom('EPSG:4326',meta['crs'],fp)).area/1e6
   self.assertAlmostEqual(area,meta['valid_comparison_area_km2'],places=6)
   with rasterio.open(directory/'classes.tif') as ds:
    a=ds.read(1)
    for code in (1,2,3):self.assertAlmostEqual(float((a==code).sum())*.0001,meta['areas'][str(code)]['area_km2'])
   self.assertLessEqual(meta['valid_comparison_area_km2'],meta['requested_area_km2']+.02)
 def test_real_classification_uses_existing_algorithm(self):
  folder=ROOT/'data/geographic_mapping/5km'
  with rasterio.open(folder/'radar_power.tif') as ds:b,a=ds.read().astype(float)
  mask=np.isfinite(b)&(b>0)&np.isfinite(a)&(a>0)
  classes,_=classify(power_to_db(mask_aware_mean(b,mask)),power_to_db(mask_aware_mean(a,mask)),mask,-16,3)
  with rasterio.open(folder/'classes.tif') as ds:np.testing.assert_array_equal(classes,ds.read(1))
 def test_map_html_layers_and_projected_display(self):
  meta,display,bounds,fp=load_geographic(ROOT/'data/geographic_mapping/5km')
  html=build_map(meta,display,bounds,fp)
  for text in ('Candidate water expansion','Candidate water recession','Persistent water candidate','OpenStreetMap','Unvalidated candidate','imageOverlay','Actual valid processed footprint'):self.assertIn(text,html)
  self.assertLess(len(html.encode()),2*1024*1024)
 def test_dashboard_page_separation_and_missing_data(self):
  app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run();apptest_open(app,'NISAR study');self.assertFalse(app.exception)  # Explore (with "Start here") is the landing page
  self.assertEqual(app.metric[0].value,'0.0569 km²')
  apptest_open(app,'Geographic map (NISAR)');self.assertFalse(app.exception)
  self.assertEqual(len(app.metric),3)
  self.assertTrue(any('Unvalidated candidate surface-water changes' in w.value for w in app.warning))
  apptest_open(app,'Benchmark Validation (Sentinel-1)');self.assertFalse(app.exception);self.assertEqual(len(app.metric),0)
  apptest_open(app,'NISAR study');self.assertEqual(app.metric[0].value,'0.0569 km²')

if __name__=='__main__':unittest.main()
