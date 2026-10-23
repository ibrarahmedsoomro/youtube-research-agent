"""
Unit Tests for VidIQ Advanced Optimization Features:
1. YouTube Live Publishing Engine (operations/youtube_publisher.py)
2. Batch Auto-Optimization Engine (audit/batch_optimizer.py)
3. Competitor Outlier & Strategic Gap Scanner (competitors/gap_scanner.py)
4. AI Thumbnail Studio & Mobile Contrast Inspector (production/thumbnail_studio.py)
"""

import unittest
from operations.youtube_publisher import YouTubePublisher
from audit.batch_optimizer import BatchOptimizer
from competitors.gap_scanner import CompetitorGapScanner
from production.thumbnail_studio import ThumbnailStudio

class TestAdvancedFeatures(unittest.TestCase):
    def setUp(self):
        self.sample_videos = [
            {
                "video_id": "v_test_01",
                "title": "Why You Should Never Find TAPE 047 #AnalogHorror",
                "views": 1500,
                "url": "https://www.youtube.com/watch?v=v_test_01",
                "thumbnail_url": "https://img.youtube.com/vi/v_test_01/hqdefault.jpg"
            },
            {
                "video_id": "v_test_02",
                "title": "Short title",
                "views": 35,
                "url": "https://www.youtube.com/watch?v=v_test_02",
                "thumbnail_url": "https://img.youtube.com/vi/v_test_02/hqdefault.jpg"
            }
        ]

    def test_youtube_publisher_sandbox(self):
        publisher = YouTubePublisher(credentials_path="non_existent_creds.json")
        res = publisher.update_video_metadata(
            video_id="test_vid_123",
            title="The Unsolved Mystery of Tape 047",
            description="Watch till the end for the hidden clue...",
            tags=["analog horror", "scary", "vhs"],
            dry_run=True
        )
        self.assertEqual(res["status"], "SANDBOX_SIMULATED_SUCCESS")
        self.assertTrue(res["is_sandbox"])
        self.assertEqual(res["updated_fields"]["tags_count"], 3)
        self.assertEqual(len(res["validation_errors"]), 0)

    def test_youtube_publisher_validation_limits(self):
        publisher = YouTubePublisher(credentials_path="non_existent_creds.json")
        # Long title over 100 chars
        long_title = "A" * 105
        res = publisher.update_video_metadata(
            video_id="test_vid_123",
            title=long_title,
            description="Short desc",
            tags=["tag1"],
            dry_run=True
        )
        self.assertEqual(res["status"], "VALIDATION_FAILED")
        self.assertTrue(any("Title exceeds" in err for err in res["validation_errors"]))

    def test_batch_optimizer_scan_and_generate(self):
        optimizer = BatchOptimizer()
        batch_res = optimizer.scan_and_generate_batch(self.sample_videos, score_threshold=85)
        
        self.assertIn("total_videos_scanned", batch_res)
        self.assertGreaterEqual(batch_res["flagged_count"], 1)
        self.assertTrue(len(batch_res["batch_items"]) > 0)
        
        first_item = batch_res["batch_items"][0]
        self.assertIn("current", first_item)
        self.assertIn("optimized", first_item)
        self.assertGreater(first_item["optimized"]["projected_overall_score"], first_item["current"]["overall_score"])

    def test_batch_optimizer_apply_batch(self):
        optimizer = BatchOptimizer()
        batch_res = optimizer.scan_and_generate_batch(self.sample_videos, score_threshold=90)
        apply_res = optimizer.apply_batch_optimizations(batch_res["batch_items"], dry_run=True)
        
        self.assertEqual(apply_res["successful_updates"], len(batch_res["batch_items"]))
        self.assertEqual(apply_res["failed_updates"], 0)

    def test_competitor_gap_scanner(self):
        scanner = CompetitorGapScanner()
        res = scanner.scan_topic_gaps(
            our_channel_videos=self.sample_videos,
            competitor_channels=["@spookytoonstories", "@Local58TV"],
            max_videos_per_competitor=5
        )
        self.assertIn("gaps_found", res)
        self.assertIn("top_gaps", res)
        if res["top_gaps"]:
            top = res["top_gaps"][0]
            self.assertIn("opportunity_score", top)
            self.assertIn("actionable_title_idea", top)
            self.assertIn("target_hook", top)

    def test_thumbnail_studio_audit(self):
        # 3 words -> passes 3-word rule
        audit_pass = ThumbnailStudio.audit_thumbnail("STOP LOOKING NOW", has_face=True, color_contrast="High")
        self.assertGreaterEqual(audit_pass["thumbnail_score"], 85)
        self.assertEqual(audit_pass["tier"], "Optimal 🟢")

        # 6 words -> fails 3-word rule
        audit_fail = ThumbnailStudio.audit_thumbnail("This Is Way Too Many Words To Read", has_face=False, color_contrast="Low")
        self.assertLess(audit_fail["thumbnail_score"], 70)
        self.assertTrue(any("3-4 words" in iss for iss in audit_fail["issues"]))

    def test_thumbnail_studio_ai_prompts(self):
        prompt_data = ThumbnailStudio.generate_ai_image_prompt(
            topic="Tape 047 Incident",
            style="Analog Horror VHS",
            aspect_ratio="9:16"
        )
        self.assertIn("midjourney_prompt", prompt_data)
        self.assertIn("imagen_prompt", prompt_data)
        self.assertIn("--ar 9:16", prompt_data["midjourney_prompt"])
        self.assertIn("negative_prompt", prompt_data)

    def test_topic_adaptive_thumbnail_concepts(self):
        # 1. World War 2 / Military niche
        ww2_concepts = ThumbnailStudio.generate_concepts(topic="World War 2")
        self.assertEqual(len(ww2_concepts), 3)
        self.assertIn("Declassified", ww2_concepts[0]["name"])
        self.assertIn("War", ww2_concepts[0]["name"])
        self.assertIn("WHAT THEY HID", ww2_concepts[0]["text_overlay"])
        self.assertIn("World War 2", ww2_concepts[0]["visual_layout"])

        # WW2 AI prompt
        ww2_prompts = ThumbnailStudio.generate_ai_image_prompt(topic="World War 2", aspect_ratio="9:16")
        self.assertIn("battlefield", ww2_prompts["midjourney_prompt"].lower())
        self.assertIn("world war 2", ww2_prompts["midjourney_prompt"].lower())
        self.assertEqual(ww2_prompts["recommended_overlay_text"], "WHAT THEY HID")

        # 2. Aviation / MH370 niche
        av_concepts = ThumbnailStudio.generate_concepts(topic="Vanished Skies MH370")
        self.assertEqual(len(av_concepts), 3)
        self.assertIn("Radar Anomaly", av_concepts[0]["name"])
        self.assertIn("THEY VANISHED", av_concepts[0]["text_overlay"])


    def test_language_detection_and_adaptive_agent(self):
        from ai.agent import detect_user_language, YouTubeAIAgent

        # 1. English default detection
        self.assertEqual(detect_user_language("How do I grow my YouTube channel fast?"), "english")
        self.assertEqual(detect_user_language("Write a script for horror story"), "english")

        # 2. Roman Urdu detection
        self.assertEqual(detect_user_language("channel par views drop kyun ho rahe hain aur kaise theek karein?"), "roman_urdu")
        self.assertEqual(detect_user_language("mujhe viral script do horror topic par"), "roman_urdu")
        self.assertEqual(detect_user_language("kya haal hy"), "roman_urdu")

        # 3. Agent adaptive responses
        agent = YouTubeAIAgent()
        
        # English query gives English response
        res_en = agent.ask_expert("How to prevent views drop in YouTube shorts?", channel_name="Vanished Skies")
        self.assertEqual(res_en.get("language"), "english")
        self.assertIn("Why Views Drop on YouTube", res_en["response_text"])

        # Roman Urdu query gives Roman Urdu response
        res_ur = agent.ask_expert("views drop kyun ho rahe hain aur iska solution batao", channel_name="Vanished Skies")
        self.assertEqual(res_ur.get("language"), "roman_urdu")
        self.assertIn("Views kyun drop hote hain", res_ur["response_text"])

if __name__ == "__main__":
    unittest.main()

