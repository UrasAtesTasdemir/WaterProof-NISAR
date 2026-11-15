"""Synthetic arrays here are unit fixtures only; never satellite outputs."""

import unittest
import numpy as np
from rasterio.crs import CRS
from rasterio.transform import Affine

from src.water_change import (align_power, class_areas, classify, mask_aware_mean,
                              pixel_area_km2, power_to_db)


class WaterChangeTests(unittest.TestCase):
    def test_db_known_values(self):
        np.testing.assert_allclose(power_to_db([1, 0.1, 0.01, 10]), [0, -10, -20, 10])

    def test_invalid_power_never_becomes_water(self):
        db = power_to_db([0, -1, np.nan, np.inf, -np.inf, 0.01])
        self.assertTrue(np.isnan(db[:5]).all())
        classes, delta = classify(db, db, np.ones(6, bool))
        np.testing.assert_array_equal(classes, [0, 0, 0, 0, 0, 1])
        self.assertTrue(np.isnan(delta[:5]).all())

    def test_all_class_transitions_and_signed_change(self):
        before = np.array([-20, -10, -20, -10, np.nan])
        after = np.array([-21, -20, -10, -11, -25])
        classes, delta = classify(before, after, np.ones(5, bool))
        np.testing.assert_array_equal(classes, [1, 2, 3, 4, 0])
        np.testing.assert_allclose(delta[:4], [-1, -10, 10, -1])

    def test_change_gate_reject_disable_and_exact_boundary(self):
        b, a = np.array([-15, -17, -13]), np.array([-17, -15, -16])
        classes, _ = classify(b, a, np.ones(3, bool))
        np.testing.assert_array_equal(classes, [4, 4, 2])
        classes, _ = classify(b, a, np.ones(3, bool), min_change=None)
        np.testing.assert_array_equal(classes, [2, 3, 2])
        classes, _ = classify(b, a, np.ones(3, bool), water_threshold=-18, min_change=None)
        np.testing.assert_array_equal(classes, [4, 4, 4])

    def test_identical_images_have_no_change(self):
        p = np.array([[0.01, 0.03, 0.1], [np.nan, 0.02, 1]])
        valid = np.isfinite(p)
        db = power_to_db(mask_aware_mean(p, valid))
        classes, delta = classify(db, db, valid, min_change=None)
        self.assertFalse(np.isin(classes, [2, 3]).any())
        np.testing.assert_array_equal(delta[valid], 0)
        self.assertEqual(classes[1, 0], 0)

    def test_mask_filter_no_zero_bias_and_no_gap_filling(self):
        p = np.full((3, 3), 2.0)
        p[1, 1] = np.nan
        mask = np.isfinite(p)
        filtered = mask_aware_mean(p, mask)
        np.testing.assert_allclose(filtered[mask], 2)
        self.assertTrue(np.isnan(filtered[1, 1]))
        self.assertTrue(np.isnan(mask_aware_mean(p, np.zeros_like(mask))).all())

    def test_filter_is_in_linear_power(self):
        p = np.array([[1., 9.]])
        filtered = mask_aware_mean(p, np.ones_like(p, bool))
        np.testing.assert_allclose(filtered, 5)
        np.testing.assert_allclose(power_to_db(filtered), 10 * np.log10(5))
        self.assertNotAlmostEqual(float(power_to_db(filtered)[0, 0]), float(power_to_db(p).mean()))

    def test_common_mask_cannot_be_overridden_by_filter(self):
        common = np.array([[True, False, True]])
        b = mask_aware_mean(np.full((1, 3), 1.), common)
        a = mask_aware_mean(np.full((1, 3), 0.01), common)
        classes, delta = classify(power_to_db(b), power_to_db(a), common)
        np.testing.assert_array_equal(classes, [[2, 0, 2]])
        self.assertTrue(np.isnan(delta[0, 1]))

    def test_projected_area_and_rotated_determinant(self):
        crs = CRS.from_epsg(32615)
        t = Affine(10, 0, 0, 0, -10, 0)
        self.assertAlmostEqual(pixel_area_km2(crs, t), 0.0001)
        areas = class_areas(np.array([[2, 2, 3, 0, 4]]), crs, t)
        self.assertAlmostEqual(areas['2']['area_km2'], 0.0002)
        self.assertAlmostEqual(areas['3']['area_km2'], 0.0001)
        self.assertAlmostEqual(pixel_area_km2(crs, Affine(10, 2, 0, 3, -10, 0)), 0.000106)

    def test_area_rejects_degrees_and_converts_projected_feet(self):
        with self.assertRaisesRegex(ValueError, 'projected'):
            pixel_area_km2(CRS.from_epsg(4326), Affine.scale(.01, -.01))
        crs = CRS.from_epsg(2263)
        factor = crs.linear_units_factor[1]
        self.assertAlmostEqual(pixel_area_km2(crs, Affine.scale(10, -10)), 100 * factor**2 / 1e6)

    def test_alignment_identical_and_shifted_grid_masks(self):
        crs = CRS.from_epsg(32615)
        target = {'crs': crs, 'transform': Affine(10, 0, 0, 0, -10, 20), 'shape': (2, 2)}
        p, v = np.array([[1., 2.], [3., 4.]]), np.ones((2, 2), bool)
        same, mask, corrected = align_power(p, v, target, target)
        self.assertFalse(corrected)
        np.testing.assert_array_equal(same, p)
        source = {**target, 'transform': Affine(10, 0, 10, 0, -10, 20)}
        shifted, mask, corrected = align_power(p, v, source, target)
        self.assertTrue(corrected)
        self.assertFalse(mask[:, 0].any())
        self.assertTrue(np.isnan(shifted[:, 0]).all())
        np.testing.assert_array_equal(shifted[:, 1], [1, 3])

    def test_bad_parameters_rejected(self):
        for size in (0, 2, 11):
            with self.assertRaises(ValueError):
                mask_aware_mean(np.ones((2, 2)), np.ones((2, 2), bool), size)
        for change in (-1, np.nan):
            with self.assertRaises(ValueError):
                classify(np.zeros(1), np.zeros(1), np.ones(1, bool), min_change=change)


if __name__ == '__main__':
    unittest.main()
