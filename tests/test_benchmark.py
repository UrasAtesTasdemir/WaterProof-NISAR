"""Benchmark unit fixtures and actual data/UI checks; never NISAR accuracy."""
import json,unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
from streamlit.testing.v1 import AppTest
from src.sentinel_benchmark import prepare_db,evaluation_mask,assert_no_leakage,load_chip,predict,otsu_threshold
from src.reference_validation import agreement
from src.navigation import apptest_open
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'data/benchmark_validation'
class BenchmarkTests(unittest.TestCase):
 def test_already_db_no_double_log(self):
  a=np.full((3,3),-20.)
  np.testing.assert_allclose(prepare_db(a,np.ones_like(a,bool)),-20)
  with self.assertRaises(ValueError):prepare_db(a,np.ones_like(a,bool),units='power')
 def test_manual_mask_and_radar_invalid(self):
  np.testing.assert_array_equal(evaluation_mask(np.array([-1,0,1,1]),[1,1,1,0]),[0,1,1,0])
 def test_confusion_matrix(self):
  m=agreement([0,1,1,0],[0,1,0,1],[1,1,1,1])
  self.assertEqual(m['matrix_rows_reference_nonwater_water_columns_prediction_nonwater_water'],[[1,1],[1,1]])
  self.assertAlmostEqual(m['F1'],.5);self.assertAlmostEqual(m['IoU'],1/3)
 def test_no_train_test_leakage(self):
  m=json.loads((P/'sample_manifest.json').read_text())
  train=[r['radar'] for r in m['records'] if r['split']=='train'];test=[r['radar'] for r in m['records'] if r['split']=='test']
  assert_no_leakage(train,test,train,test)
  with self.assertRaises(ValueError):assert_no_leakage(['x'],['x'],['x'],['x'])
  with self.assertRaises(ValueError):assert_no_leakage(['z'],['x'],['y'],['x'])
 def test_missing_data_preserved(self):
  a=np.full((3,3),-20.);a[1,1]=np.nan
  db=prepare_db(a,np.isfinite(a));self.assertTrue(np.isnan(db[1,1]));self.assertFalse(predict(db,-19)[1,1])
  self.assertTrue(np.isnan(prepare_db(a,np.zeros_like(a,bool))).all())
  with self.assertRaises((OSError,ValueError)):load_chip(P/'missing.tif',P/'missing_label.tif')
 def test_frozen_calibration_matches_train_only_grid(self):
  c=json.loads((P/'calibration.json').read_text());grid=json.loads((P/'training_grid.json').read_text());best=max(grid,key=lambda r:r['training_macro_F1'])
  self.assertEqual(c['band'],best['band']);self.assertEqual(c['threshold_db'],best['threshold_db']);self.assertEqual(c['calibration_split'],'official train subset')
 def test_actual_heldout_counts_and_micro_scores(self):
  r=json.loads((P/'results.json').read_text());self.assertEqual(r['test_scenes'],12)
  matrix=np.sum([x['metrics']['matrix_rows_reference_nonwater_water_columns_prediction_nonwater_water'] for x in r['test_scene_metrics']],axis=0)
  np.testing.assert_array_equal(matrix,r['test_micro_metrics']['matrix_rows_reference_nonwater_water_columns_prediction_nonwater_water'])
  self.assertEqual(int(matrix.sum()),r['test_valid_pixels']);self.assertTrue((P/'figures'/(r['worst_scene']+'.png')).exists())
 def test_otsu_requires_no_labels(self):
  x=np.array([[-30.,-29.,-5.,-4.]])
  t=otsu_threshold(x);self.assertTrue(-30<t<-4)
  with self.assertRaises(ValueError):otsu_threshold(np.array([np.nan]))
 def test_optional_ui_keeps_metrics_separate(self):
  with patch('requests.sessions.Session.request',side_effect=AssertionError('Network disabled')):
   app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run();apptest_open(app,'NISAR study');self.assertFalse(app.exception)  # Explore (with "Start here") is the landing page
   self.assertEqual(app.metric[0].value,'0.0569 km²')
   apptest_open(app,'Benchmark Validation (Sentinel-1)')
   self.assertFalse(app.exception);self.assertEqual(len(app.metric),0)
   self.assertTrue(any('NOT establish NISAR' in x.value for x in app.warning))
   self.assertTrue(app.table)
   apptest_open(app,'NISAR study');self.assertFalse(app.exception)
   self.assertEqual(app.metric[0].value,'0.0569 km²')
if __name__=='__main__':unittest.main()
