"""
Unit tests for Transcript Intelligence, Topic Clustering & Opportunity Engine.
"""

import unittest
from scraper.models import VideoTranscript, TranscriptSegment, VideoMetadata
from research.transcript_intelligence import TranscriptIntelligenceEngine
from research.topic_clustering import TopicClusteringEngine
from research.opportunity_finder import OpportunityFinder
from analytics.seo_scorer import SEOReadinessEvaluator


class TestIntelligenceEngine(unittest.TestCase):
    def test_transcript_decomposition(self):
        segments = [
            TranscriptSegment(text="Why did Flight 19 vanish in 1945 without a trace?", start=0.0, duration=5.0),
            TranscriptSegment(text="In this video we analyze the declassified Navy reports.", start=5.0, duration=8.0),
            TranscriptSegment(text="Here is the core promise and what you will discover.", start=16.0, duration=15.0),
            TranscriptSegment(text="But here is the twist that nobody told you about.", start=45.0, duration=10.0),
            TranscriptSegment(text="Suddenly all radar contacts ceased.", start=120.0, duration=8.0),
            TranscriptSegment(text="In conclusion, the mystery remains unresolved. Subscribe for more.", start=560.0, duration=30.0),
        ]
        t_obj = VideoTranscript(
            video_id="test_vid_1",
            full_text=" ".join([s.text for s in segments]),
            segments=segments,
        )

        analysis = TranscriptIntelligenceEngine.analyze_transcript(t_obj, duration_seconds=600)
        self.assertTrue(analysis["has_transcript"])
        self.assertIn("Curiosity Question", analysis["hook"]["type"])
        self.assertGreater(analysis["pattern_interrupts"]["count"], 0)
        self.assertEqual(analysis["confidence"], "MEDIUM")

    def test_topic_clustering(self):
        sample_videos = [
            {"video_id": "v1", "title": "Bermuda Triangle Flight 19 Mystery", "views": 100000, "age_adjusted_outlier": 4.5, "is_outlier": True, "url": "http://yt/1"},
            {"video_id": "v2", "title": "What Happened To Flight 19 in Bermuda Triangle?", "views": 85000, "age_adjusted_outlier": 3.8, "is_outlier": True, "url": "http://yt/2"},
            {"video_id": "v3", "title": "Top 10 Aviation Mysteries Ever", "views": 20000, "age_adjusted_outlier": 1.1, "is_outlier": False, "url": "http://yt/3"},
            {"video_id": "v4", "title": "Deep Ocean Mariana Trench Creatures", "views": 30000, "age_adjusted_outlier": 1.2, "is_outlier": False, "url": "http://yt/4"},
        ]
        clusters = TopicClusteringEngine.cluster_videos(sample_videos, min_cluster_size=2)
        self.assertGreater(len(clusters), 0)
        
        c = clusters[0]
        self.assertIn("cluster_name", c)
        self.assertIn("outlier_count", c)
        self.assertIn("median_views", c)

    def test_opportunity_scoring_and_evidence(self):
        cluster = {
            "cluster_id": "c1",
            "cluster_name": "Bermuda Triangle Flight 19",
            "video_count": 4,
            "competitor_count": 2,
            "median_views": 80000.0,
            "avg_views": 90000.0,
            "outlier_count": 2,
            "outlier_ratio_avg": 4.1,
            "dominant_creators": ["AviationFiles", "MysteryChannel"],
            "sample_videos": [
                {"title": "Flight 19 Vanished", "views": 100000, "outlier_ratio": 4.5, "url": "http://yt/1"},
                {"title": "Bermuda Triangle Truth", "views": 85000, "outlier_ratio": 3.8, "url": "http://yt/2"},
            ]
        }
        opp = OpportunityFinder.score_cluster_opportunity(cluster, niche="Aviation Mysteries", channel_median_views=15000.0)
        self.assertGreater(opp["opportunity_score"], 60.0)
        self.assertIn(opp["confidence"], ["HIGH", "MEDIUM"])
        self.assertGreater(len(opp["evidence_ledger"]), 0)
        self.assertEqual(opp["evidence_ledger"][0]["metric_name"], "Outlier Multiplier")

    def test_seo_readiness_evaluator(self):
        meta = VideoMetadata(
            video_id="test_seo_1",
            title="How To Solve Cold Cases in 5 Simple Steps [Guide]",
            channel_name="TrueCrimeCases",
            url="http://yt/test",
            description="In this step by step guide we explore how investigators solve cold cases using forensic science and archival evidence. 0:00 Intro\n2:15 Forensic Methods\n6:30 Summary",
            tags=["cold cases", "how to solve cold cases", "forensic science", "investigation tutorial", "true crime guide"],
            has_captions=True,
        )
        eval_res = SEOReadinessEvaluator.evaluate_video(meta, target_query="how to solve cold cases")
        self.assertEqual(eval_res["readiness_rating"], "HIGH READINESS")
        self.assertEqual(eval_res["intent_category"], "How-To / Educational")


if __name__ == "__main__":
    unittest.main()
