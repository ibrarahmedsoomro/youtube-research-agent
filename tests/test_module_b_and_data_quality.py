"""
Unit tests for Module B (Channel/Video Optimization) & Data Quality Engine.
"""

import unittest
from analytics.data_quality import DataQualityEngine
from production.title_intelligence import TitleIntelligenceEngine
from production.thumbnail_intelligence import ThumbnailIntelligenceEngine
from production.description_keyword_engine import DescriptionKeywordEngine
from learning.channel_learning import ChannelLearningEngine


class TestModuleBAndDataQuality(unittest.TestCase):
    def test_data_quality_validation(self):
        sample_videos = [
            {"video_id": "v1", "views": 1000, "comments": 50, "transcript": "Hello world", "data_age_hours": 12.0},
            {"video_id": "v1", "views": 1000, "comments": 50}, # Duplicate
            {"video_id": "v2", "views": -1, "comments": 10}, # Missing views
            {"video_id": "v3", "views": 5000, "comments": -1, "data_age_hours": 2500.0} # Stale & missing comments
        ]
        res = DataQualityEngine.validate_video_dataset(sample_videos, run_id="test_run_1")
        self.assertEqual(len(res["valid_videos"]), 3)
        self.assertEqual(res["duplicate_count"], 1)
        self.assertEqual(res["missing_views_count"], 1)
        self.assertEqual(res["missing_comments_count"], 1)
        self.assertIn("v2", [v["video_id"] for v in res["valid_videos"]])
        # Verify non-imputation
        v2 = next(v for v in res["valid_videos"] if v["video_id"] == "v2")
        self.assertEqual(v2["views_status"], "UNKNOWN")

    def test_title_intelligence_analysis(self):
        analysis = TitleIntelligenceEngine.analyze_title(
            title="The Terrifying Truth About AI Agents Nobody Talks About",
            target_keyword="AI Agents"
        )
        self.assertFalse(analysis["mobile_cutoff_risk"])
        self.assertGreaterEqual(analysis["curiosity_score"], 60.0)
        self.assertIn("truth", analysis["power_words_found"])
        self.assertTrue(analysis["keyword_frontloaded"])

    def test_title_candidate_generator(self):
        candidates = TitleIntelligenceEngine.generate_candidate_titles("Analog Horror", target_keyword="Analog Horror")
        self.assertEqual(len(candidates), 5)
        archetypes = [c["archetype"] for c in candidates]
        self.assertIn("Contrarian / Mythbuster", archetypes)
        self.assertIn("High Stakes / Warning", archetypes)

    def test_thumbnail_intelligence(self):
        audit = ThumbnailIntelligenceEngine.audit_thumbnail_concept(
            focal_element="Expressive Human Face",
            background_style="High Contrast Dark Background",
            text_overlay="DON'T DO THIS"
        )
        self.assertTrue(audit["mobile_preview_pass"])
        self.assertEqual(audit["text_clutter_level"], "OPTIMAL (1-4 WORDS)")
        self.assertTrue(audit["duration_badge_safety_checked"])

    def test_description_and_keyword_audit(self):
        desc = (
            "In this video we break down the secrets of YouTube growth.\n\n"
            "Timestamps:\n0:00 - Introduction\n01:30 - The Strategy\n05:45 - Case Study\n\n"
            "Subscribe for more content: https://youtube.com"
        )
        audit = DescriptionKeywordEngine.audit_description(desc, video_id="vid_123")
        self.assertTrue(audit["above_the_fold_pass"])
        self.assertTrue(audit["has_timestamps"])
        self.assertTrue(audit["has_cta"])
        self.assertTrue(audit["has_links"])

    def test_channel_learning_signals(self):
        videos = [
            {"video_id": "v1", "title": "The Analog Horror Mystery", "views": 100000, "age_adjusted_outlier": 4.5, "outlier_tier": "STRONG OUTLIER", "duration_seconds": 600},
            {"video_id": "v2", "title": "Another Analog Horror Story", "views": 80000, "age_adjusted_outlier": 3.2, "outlier_tier": "STRONG OUTLIER", "duration_seconds": 720},
            {"video_id": "v3", "title": "Regular Video", "views": 15000, "age_adjusted_outlier": 1.0, "outlier_tier": "NORMAL", "duration_seconds": 300},
            {"video_id": "v4", "title": "Another Upload", "views": 18000, "age_adjusted_outlier": 1.1, "outlier_tier": "NORMAL", "duration_seconds": 650},
            {"video_id": "v5", "title": "Video 5", "views": 12000, "age_adjusted_outlier": 0.9, "outlier_tier": "NORMAL", "duration_seconds": 580},
        ]
        signals = ChannelLearningEngine.extract_channel_learning_signals("@testchannel", videos)
        self.assertGreaterEqual(len(signals), 2)
        signal_types = [s["signal_type"] for s in signals]
        self.assertIn("top_outlier_themes", signal_types)
        self.assertIn("optimal_duration_sweetspot", signal_types)


    def test_approval_center(self):
        from operations.approval_center import ApprovalCenter
        res = ApprovalCenter.create_approval_entry(
            title="Test Video For Approval",
            format_type="Long-form",
            prepublish_score=95.0,
            policy_risk="LOW",
            notes="Ready for review"
        )
        self.assertIn("id", res)
        all_apprs = ApprovalCenter.get_all_approvals()
        self.assertGreaterEqual(len(all_apprs), 1)
        found = any(a["title"] == "Test Video For Approval" for a in all_apprs)
        self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
