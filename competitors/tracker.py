"""
Competitor Tracker Engine.
Monitors multiple channels, calculates baselines, identifies breakout outlier videos,
and extracts trending themes worth replicating.
"""

from typing import List, Dict, Any, Optional
from collections import Counter
import re

from scraper.channel_scraper import ChannelScraper
from scraper.models import ChannelVideoSummary
from analytics.metrics import calculate_channel_baseline, calculate_outlier_score


class CompetitorTracker:
    def __init__(self):
        self.channel_scraper = ChannelScraper()

    def analyze_channel(self, channel_identifier: str, max_videos: int = 15) -> Dict[str, Any]:
        """
        Analyzes a single channel: fetches recent videos, computes baseline median,
        and calculates outlier multipliers for every video.
        """
        videos = self.channel_scraper.fetch_channel_videos(channel_identifier, limit=max_videos)
        if not videos:
            return {
                "channel_identifier": channel_identifier,
                "median_views": 0,
                "video_count": 0,
                "videos": [],
                "breakouts": [],
            }

        views_list = [v.views for v in videos if v.views and v.views > 0]
        baseline = calculate_channel_baseline(views_list)
        median_views = baseline["median_views"]

        analyzed_videos = []
        breakouts = []

        for v in videos:
            outlier_info = calculate_outlier_score(v.views or 0, median_views)
            item = {
                "video_id": v.video_id,
                "url": v.url,
                "title": v.title,
                "views": v.views or 0,
                "duration_text": v.duration_text,
                "published_time_text": v.published_time_text,
                "outlier_multiplier": outlier_info["outlier_multiplier"],
                "badge": outlier_info["badge"],
                "is_breakout": outlier_info["is_breakout"],
            }
            analyzed_videos.append(item)
            if outlier_info["is_breakout"] or outlier_info["outlier_multiplier"] >= 2.0:
                breakouts.append(item)

        return {
            "channel_identifier": channel_identifier,
            "median_views": int(median_views),
            "video_count": len(videos),
            "videos": analyzed_videos,
            "breakouts": breakouts,
        }

    def track_multiple_channels(
        self, channel_identifiers: List[str], max_videos_per_channel: int = 10
    ) -> Dict[str, Any]:
        """
        Monitors multiple competitor channels simultaneously and consolidates breakout videos.
        """
        all_breakouts: List[Dict[str, Any]] = []
        all_videos: List[Dict[str, Any]] = []
        channel_summaries: List[Dict[str, Any]] = []

        for ch in channel_identifiers:
            clean_ch = ch.strip()
            if not clean_ch:
                continue

            ch_data = self.analyze_channel(clean_ch, max_videos=max_videos_per_channel)
            channel_summaries.append(
                {
                    "channel": clean_ch,
                    "median_views": ch_data["median_views"],
                    "video_count": ch_data["video_count"],
                    "breakouts_count": len(ch_data["breakouts"]),
                }
            )

            for v in ch_data["videos"]:
                v_with_channel = dict(v)
                v_with_channel["channel"] = clean_ch
                all_videos.append(v_with_channel)

            for b in ch_data["breakouts"]:
                b_with_channel = dict(b)
                b_with_channel["channel"] = clean_ch
                all_breakouts.append(b_with_channel)

        # Sort all videos by outlier multiplier descending
        all_videos.sort(key=lambda x: x["outlier_multiplier"], reverse=True)
        all_breakouts.sort(key=lambda x: x["outlier_multiplier"], reverse=True)

        # Extract trending keywords from breakout video titles
        breakout_words: List[str] = []
        stop_words = {
            "the", "in", "to", "for", "and", "a", "of", "how", "with", "full", "course",
            "tutorial", "guide", "free", "best", "is", "you", "your", "what", "on", "from"
        }
        for b in all_breakouts:
            words = re.findall(r"[A-Za-z]{3,}", b["title"].lower())
            for w in words:
                if w not in stop_words:
                    breakout_words.append(w)

        top_themes = [
            {"keyword": kw, "frequency": count}
            for kw, count in Counter(breakout_words).most_common(8)
        ]

        return {
            "total_channels": len(channel_summaries),
            "channels": channel_summaries,
            "total_videos_analyzed": len(all_videos),
            "total_breakouts_found": len(all_breakouts),
            "top_outliers": all_videos[:15],
            "breakout_videos": all_breakouts,
            "trending_themes": top_themes,
        }
