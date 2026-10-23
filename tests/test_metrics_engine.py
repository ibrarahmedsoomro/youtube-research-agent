"""
Unit tests for Deterministic Performance & Outlier Engine.
"""

import unittest
from analytics.metrics import (
    get_age_cohort,
    calculate_expected_views_for_age,
    calculate_age_normalized_outlier,
    calculate_video_features,
    calculate_channel_baseline,
)


class TestMetricsEngine(unittest.TestCase):
    def test_age_cohorts(self):
        self.assertEqual(get_age_cohort(2.0)["name"], "0-6h")
        self.assertEqual(get_age_cohort(12.0)["name"], "6-24h")
        self.assertEqual(get_age_cohort(48.0)["name"], "1-3d")
        self.assertEqual(get_age_cohort(120.0)["name"], "3-7d")
        self.assertEqual(get_age_cohort(300.0)["name"], "7-30d")
        self.assertEqual(get_age_cohort(1000.0)["name"], "30-90d")
        self.assertEqual(get_age_cohort(5000.0)["name"], "90d+")

    def test_expected_view_decay_curve(self):
        median = 10000.0
        # Fresh video (2 hours) should have low expected view baseline
        exp_2h = calculate_expected_views_for_age(median, 2.0)
        # 1 day old video (24 hours)
        exp_24h = calculate_expected_views_for_age(median, 24.0)
        # 7 days old video (168 hours) completes the burst phase near channel median
        exp_168h = calculate_expected_views_for_age(median, 168.0)
        # 30 days old video (720 hours) accumulates evergreen views beyond the 7-day burst
        exp_720h = calculate_expected_views_for_age(median, 720.0)

        self.assertLess(exp_2h, exp_24h)
        self.assertLess(exp_24h, exp_168h)
        self.assertLess(exp_168h, exp_720h)
        self.assertAlmostEqual(exp_168h, median, delta=500.0)
        self.assertGreater(exp_720h, exp_168h)

    def test_age_normalized_outlier(self):
        # A 6-hour old video with 10,000 views when expected is 2,000 -> 5.0x Outlier
        outlier = calculate_age_normalized_outlier(actual_views=10000, expected_views=2000.0, sample_size=30)
        self.assertEqual(outlier["tier"], "EXTREME OUTLIER")
        self.assertTrue(outlier["is_outlier"])
        self.assertEqual(outlier["confidence"], "HIGH")

        # A video with normal expected performance
        normal = calculate_age_normalized_outlier(actual_views=2100, expected_views=2000.0, sample_size=15)
        self.assertEqual(normal["tier"], "NORMAL")
        self.assertFalse(normal["is_outlier"])

    def test_video_features_extraction(self):
        features = calculate_video_features(
            views=50000,
            likes=2500,
            comments=400,
            age_hours=48.0,
            channel_median_views=10000.0,
            subscriber_count=100000,
            channel_sample_size=20,
        )
        self.assertEqual(features["views"], 50000)
        self.assertGreater(features["views_per_hour"], 0)
        self.assertGreater(features["engagement_rate_percent"], 0)
        self.assertEqual(features["cohort"], "1-3d")
        self.assertIn("outlier_tier", features)


if __name__ == "__main__":
    unittest.main()
