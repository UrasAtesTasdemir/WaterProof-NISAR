"""Reference agreement fixtures are synthetic test arrays, never observations."""
import json,unittest
from pathlib import Path
import numpy as np
from rasterio.crs import CRS
from rasterio.transform import Affine
from src.reference_validation import agreement,align_categories,reference_valid,eligibility

class ReferenceValidationTests(unittest.TestCase):
 def test_known_confusion_matrix(self):
  m=agreement([0,1,0,1],[0,0,1,1],np.ones(4,bool))
  self.assertEqual(m['matrix_rows_reference_nonwater_water_columns_prediction_nonwater_water'],[[1,1],[1,1]])
  self.assertAlmostEqual(m['precision'],.5);self.assertAlmostEqual(m['recall'],.5)
  self.assertAlmostEqual(m['F1'],.5);self.assertAlmostEqual(m['IoU'],1/3)
 def test_unknowns_excluded(self):
  v=np.array([0,1,3,250,251,254,255])
  np.testing.assert_array_equal(reference_valid(v,'S1'),[1,1,1,0,0,0,0])
  np.testing.assert_array_equal(reference_valid(np.array([0,1,2,252,253,254,255]),'HLS'),[1,1,1,0,0,0,0])
  m=agreement([0,1,1],[0,1,0],[1,1,0]);self.assertEqual(m['valid_pixels'],2);self.assertEqual(m['IoU'],1)
 def test_undefined_scores_not_fabricated(self):
  with self.assertRaises(ValueError):agreement([1],[1],[0])
  m=agreement([0],[0],[1])
  self.assertIsNone(m['precision']);self.assertIsNone(m['recall']);self.assertIsNone(m['F1']);self.assertIsNone(m['IoU'])
 def test_categorical_nearest_preserves_codes(self):
  source={'crs':CRS.from_epsg(32615),'transform':Affine(30,0,0,0,-30,60),'shape':(2,2)}
  target={**source,'transform':Affine(15,0,0,0,-15,60),'shape':(4,4)}
  a=np.array([[0,1],[3,255]],dtype='uint8');b=align_categories(a,source,target)
  np.testing.assert_array_equal(b,np.repeat(np.repeat(a,2,0),2,1))
 def test_temporal_and_coverage_gate(self):
  self.assertTrue(eligibility(-11,.99));self.assertFalse(eligibility(131,1))
  self.assertFalse(eligibility(5,0));self.assertFalse(eligibility(53,.56))
 def test_real_attempt_has_no_unsupported_scores(self):
  p=Path(__file__).resolve().parents[1]/'data/validation/validation_results.json'
  j=json.loads(p.read_text())
  self.assertFalse(j['quantitative_validation_possible'])
  self.assertIsNone(j['agreement_metrics']);self.assertIsNone(j['expansion_recession_agreement'])
  s=next(r for r in j['reference_inventory'] if 'DSWX-S1' in r['collection'] and r['acquisition_utc'].startswith('2026-06-21'))
  self.assertEqual(s['valid_reference_pixels'],0)
  self.assertEqual(s['aoi_pixel_centers'],15424)

if __name__=='__main__':unittest.main()
