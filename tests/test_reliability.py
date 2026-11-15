"""Unit fixtures and real-data UI regression for optional size filtering."""
import unittest
import numpy as np
from streamlit.testing.v1 import AppTest
from src.water_change import suppress_single_pixel_changes
from src.dashboard_data import prepare_data,calculate,sensitivity,ROOT
from src.navigation import apptest_open

class ReliabilityTests(unittest.TestCase):
    def test_separate_classes_and_diagonal_connectivity(self):
        a=np.array([[2,0,0,0],[0,2,0,3],[0,0,1,4],[2,3,0,0]],dtype='uint8')
        source=a.copy();out,mask=suppress_single_pixel_changes(a)
        self.assertEqual(out[0,0],2);self.assertEqual(out[1,1],2)
        self.assertEqual(out[3,0],4);self.assertEqual(out[3,1],4);self.assertEqual(out[1,3],4)
        np.testing.assert_array_equal(a,source)
        np.testing.assert_array_equal(out[a==0],0)
        self.assertEqual(out[2,2],1);self.assertEqual(mask.sum(),3)

    def test_identical_or_unknown_maps_unchanged(self):
        for value in (0,1,4):
            a=np.full((3,3),value,dtype='uint8')
            out,mask=suppress_single_pixel_changes(a)
            np.testing.assert_array_equal(out,a);self.assertFalse(mask.any())

    def test_real_singleton_counts_and_default_preserved(self):
        d=prepare_data();b=calculate(d,-16,3);r=calculate(d,-16,3,True)
        self.assertAlmostEqual(b['expansion'],.0569)
        self.assertAlmostEqual(r['expansion'],.0508)
        self.assertAlmostEqual(r['recession'],.0002)
        self.assertEqual(r['suppressed_pixels'],64)
        np.testing.assert_array_equal(b['classes']==0,r['classes']==0)
        np.testing.assert_array_equal(b['delta'],r['delta'])
        self.assertEqual(r['valid_area'],b['valid_area'])
        curve=sensitivity(d,3,True)
        row=next(v for v in curve if v['Threshold (dB)']==-16)
        self.assertAlmostEqual(row['Expansion (km²)'],r['expansion'])

    def test_toggle_updates_metrics_and_reverts(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run();apptest_open(app,'NISAR study')  # Explore (with "Start here") is the landing page
        self.assertFalse(app.exception)
        self.assertFalse(app.toggle(key='remove_singletons').value)
        self.assertEqual(app.metric[0].value,'0.0569 km²')
        app.toggle(key='remove_singletons').set_value(True).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value,'0.0508 km²')
        self.assertEqual(app.metric[1].value,'0.0002 km²')
        self.assertTrue(any('64 isolated' in x.value for x in app.info))
        app.toggle(key='remove_singletons').set_value(False).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value,'0.0569 km²')

if __name__=='__main__':unittest.main()
