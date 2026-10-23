"""
Unit tests for analytics/scoring_engine.py
Tests the 4 pure deterministic scoring functions:
- score_keyword
- score_title
- score_content
- score_channel
"""

import unittest
from analytics.scoring_engine import (
    score_keyword,
    score_title,
    score_content,
    score_channel,
    outlier_multiplier,
    KeywordSignals,
    ResultVideo,
    VideoRec,
    RUBRIC_VERSION,
)


class TestScoringEngine(unittest.TestCase):
    def test_score_keyword(self):
        sig = KeywordSignals(
            keyword="analog horror",
            autocomplete_position=2,
            trends_index=85.0,
            top_results=[
                ResultVideo(title="Analog Horror Tape 01", views=50000, age_days=10.0, channel_subs=50000),
                ResultVideo(title="Why Analog Horror is Scary", views=120000, age_days=30.0, channel_subs=200000),
                ResultVideo(title="Best Analog Horror 2026", views=8000, age_days=5.0, channel_subs=5000),
            ],
            user_channel_subs=1000,
        )
        res = score_keyword(sig)
        self.assertEqual(res["keyword"], "analog horror")
        self.assertIsInstance(res["overall"], int)
        self.assertGreaterEqual(res["overall"], 0)
        self.assertLessEqual(res["overall"], 100)
        self.assertIn("band", res)
        self.assertIn("coverage", res)
        self.assertEqual(res["truth_label"], "estimated")
        self.assertEqual(res["rubric_version"], RUBRIC_VERSION)

    def test_score_title(self):
        # Optimal title (40-65 chars, curiosity, front-loaded keyword, specificity, clean hygiene)
        good_title = "The Secret of TAPE 047: Why Nobody Was Supposed To Find This"
        res = score_title(good_title, primary_kw="TAPE 047")
        self.assertGreaterEqual(res["score"], 60)
        self.assertIn(res["band"], ["great", "good", "fair"])
        self.assertIsInstance(res["parts"], dict)
        self.assertEqual(res["chars"], len(good_title))
        self.assertEqual(res["truth_label"], "rubric")

        # Short vague title
        bad_title = "cool video"
        bad_res = score_title(bad_title)
        self.assertLess(bad_res["score"], res["score"])
        self.assertTrue(len(bad_res["tips"]) > 0)

    def test_score_content(self):
        # Good description with valid chapters, hashtags, above fold hook
        desc = (
            "Watch what happens when you uncover the secret tape.\n"
            "Subscribe for weekly analog horror stories.\n\n"
            "Timestamps:\n"
            "0:00 - The Warning\n"
            "0:25 - The First Signal\n"
            "0:50 - The Final Broadcast\n\n"
            "#analoghorror #vhs #scary #horrorstories"
        )
        tags = ["analog horror", "scary", "vhs horror", "creepypasta", "dark animation"]
        res = score_content(desc, tags=tags, primary_kw="secret tape")
        self.assertGreaterEqual(res["score"], 60)
        self.assertIn("parts", res)
        self.assertEqual(res["parts"]["chapters"], 100)
        self.assertEqual(res["parts"]["above_fold"], 100)

    def test_score_channel(self):
        # Create 10 videos
        videos = []
        for i in range(1, 15):
            videos.append(
                VideoRec(
                    id=f"v_{i}",
                    title=f"Analog Horror Episode {i}: The Unseen Tape",
                    views=1000 * i,
                    age_days=float(i * 7),
                    likes=100 * i,
                    comments=10 * i,
                    format="short",
                    description="0:00 - Start\n0:15 - Middle\n0:30 - End\n#horror #vhs",
                    tags=["horror", "vhs", "analog"],
                )
            )

        res = score_channel(subs=5000, videos=videos, fmt="short")
        self.assertIn("score", res)
        self.assertIn("pillars", res)
        self.assertIn("top_issues", res)
        self.assertEqual(res["truth_label"], "rubric")
        self.assertEqual(res["rubric_version"], RUBRIC_VERSION)


if __name__ == "__main__":
    unittest.main()
