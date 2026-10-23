"""
Integration tests for Central Research Orchestrator.
"""

import unittest
from unittest.mock import MagicMock
from orchestration.orchestrator import ResearchOrchestrator
from scraper.models import VideoMetadata


class TestResearchOrchestrator(unittest.TestCase):
    def test_orchestrator_pipeline_execution(self):
        orchestrator = ResearchOrchestrator()
        
        # Mock deterministic video scraper
        mock_videos = [
            VideoMetadata(
                video_id="vid_101",
                url="https://youtube.com/watch?v=vid_101",
                title="Analog Horror Lost Broadcasts Incident 1997",
                channel_name="HorrorArchivist",
                views=150000,
                likes=12000,
                comment_count=1400,
                upload_date="20250101",
                description="The true story of the lost 1997 emergency broadcast. 0:00 Intro 1:45 The Signal 5:30 Conclusion",
                tags=["analog horror", "lost broadcast", "creepy vhs", "emergency alert system"],
                has_captions=True,
            ),
            VideoMetadata(
                video_id="vid_102",
                url="https://youtube.com/watch?v=vid_102",
                title="Why Was This 1997 Lost Broadcast Banned Everywhere?",
                channel_name="DarkHistoryHub",
                views=120000,
                likes=9500,
                comment_count=980,
                upload_date="20250115",
                description="Exploring the mysterious 1997 television takeover.",
                tags=["analog horror", "banned broadcast", "vhs mystery"],
                has_captions=True,
            ),
            VideoMetadata(
                video_id="vid_103",
                url="https://youtube.com/watch?v=vid_103",
                title="Beginner Guide To Video Editing In Premiere",
                channel_name="EditingTips",
                views=8000,
                likes=300,
                comment_count=40,
                upload_date="20250201",
                description="Tutorial on cutting video tracks.",
                tags=["video editing", "premiere tutorial"],
                has_captions=False,
            ),
        ]
        orchestrator.video_scraper.search_videos = MagicMock(return_value=mock_videos)

        result = orchestrator.execute_research_pipeline(
            query_or_channel="Analog Horror Lost Broadcasts",
            max_videos=10,
            channel_median_views=15000.0,
        )

        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["total_videos_analyzed"], 3)
        self.assertGreater(result["outliers_found"], 0)
        self.assertGreater(len(result["opportunities"]), 0)
        
        # Verify first opportunity contains observable features and evidence ledger
        top_opp = result["opportunities"][0]
        self.assertIn("observable_features", top_opp)
        self.assertIn("evidence_ledger", top_opp)
        self.assertGreater(len(top_opp["evidence_ledger"]), 0)
        self.assertIn("executive_brief", result)


if __name__ == "__main__":
    unittest.main()
