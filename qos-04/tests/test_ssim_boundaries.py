"""Check that the reference loop and convolution use the same image borders."""

import importlib.util
import unittest
from pathlib import Path

import numpy as np

CORE = Path(__file__).resolve().parents[1] / "qos_04" / "lib" / "core.py"
spec = importlib.util.spec_from_file_location("image_metrics", CORE)
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


class SSIMBoundaryTests(unittest.TestCase):
    def test_edge_distortion_matches_between_implementations(self):
        original = np.arange(35, dtype=float).reshape(5, 7) * 7
        degraded = original.copy()
        degraded[0, :] = 255
        degraded[:, -1] = 0
        for size in (3, 7, 11):
            with self.subTest(window_size=size):
                np.testing.assert_allclose(
                    metrics.ssim_loop(original, degraded, window_size=size),
                    metrics.ssim(original, degraded, window_size=size),
                    rtol=1e-10,
                    atol=1e-12,
                )

    def test_identical_flat_images_have_unit_similarity(self):
        for value in (0, 128, 255):
            original = np.full((5, 7), value, dtype=np.uint8)
            with self.subTest(value=value):
                self.assertAlmostEqual(metrics.ssim(original, original), 1)
                self.assertAlmostEqual(metrics.ssim_loop(original, original), 1)


if __name__ == "__main__":
    unittest.main()
