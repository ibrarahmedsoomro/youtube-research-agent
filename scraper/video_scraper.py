"""
Video Scraper Engine using yt-dlp.
Extracts deep metadata (views, likes, tags, descriptions, upload date, duration)
and performs keyword searches without any YouTube Data API key.
"""

import re
from typing import List, Optional, Dict, Any
import yt_dlp

from .models import VideoMetadata


class VideoScraper:
    def __init__(self):
        # yt-dlp options for metadata extraction without downloading any video/audio
        self.ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "ignoreerrors": True,
            "no_color": True,
        }

    @staticmethod
    def extract_video_id(url_or_id: str) -> str:
        """
        Normalize video ID from various YouTube URL formats or plain ID.
        """
        url_or_id = url_or_id.strip()
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"youtu\.be\/([0-9A-Za-z_-]{11})",
            r"^([0-9A-Za-z_-]{11})$",
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        return url_or_id

    def fetch_video_details(self, video_url_or_id: str) -> Optional[VideoMetadata]:
        """
        Fetches full metadata for a single YouTube video.
        """
        video_id = self.extract_video_id(video_url_or_id)
        video_url = f"https://www.youtube.com/watch?v=video_id".replace("video_id", video_id)

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info: Optional[Dict[str, Any]] = ydl.extract_info(video_url, download=False)
                if not info:
                    return None

                return VideoMetadata(
                    video_id=info.get("id", video_id),
                    url=video_url,
                    title=info.get("title", ""),
                    channel_name=info.get("channel", info.get("uploader", "")),
                    channel_id=info.get("channel_id"),
                    channel_url=info.get("channel_url", info.get("uploader_url")),
                    subscriber_count=info.get("channel_follower_count"),
                    views=info.get("view_count") or 0,
                    likes=info.get("like_count") or 0,
                    comment_count=info.get("comment_count") or 0,
                    upload_date=info.get("upload_date"),
                    timestamp=info.get("timestamp"),
                    duration_seconds=info.get("duration") or 0,
                    tags=info.get("tags") or [],
                    categories=info.get("categories") or [],
                    description=info.get("description") or "",
                    thumbnail_url=info.get("thumbnail"),
                    has_captions=bool(info.get("subtitles") or info.get("automatic_captions")),
                )
        except Exception as e:
            print(f"[VideoScraper] Error fetching details for {video_url}: {e}")
            return None

    def search_videos(self, query: str, max_results: int = 10) -> List[VideoMetadata]:
        """
        Searches YouTube for a keyword and returns list of VideoMetadata.
        """
        search_query = f"ytsearch{max_results}:{query}"
        results: List[VideoMetadata] = []

        try:
            # We use extract_flat=False to get view_count, tags, and metrics for each result
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                search_data = ydl.extract_info(search_query, download=False)
                if not search_data or "entries" not in search_data:
                    return results

                for entry in search_data["entries"]:
                    if not entry:
                        continue
                    v_id = entry.get("id", "")
                    results.append(
                        VideoMetadata(
                            video_id=v_id,
                            url=f"https://www.youtube.com/watch?v={v_id}",
                            title=entry.get("title", ""),
                            channel_name=entry.get("channel", entry.get("uploader", "")),
                            channel_id=entry.get("channel_id"),
                            channel_url=entry.get("channel_url", entry.get("uploader_url")),
                            subscriber_count=entry.get("channel_follower_count"),
                            views=entry.get("view_count") or 0,
                            likes=entry.get("like_count") or 0,
                            comment_count=entry.get("comment_count") or 0,
                            upload_date=entry.get("upload_date"),
                            timestamp=entry.get("timestamp"),
                            duration_seconds=entry.get("duration") or 0,
                            tags=entry.get("tags") or [],
                            categories=entry.get("categories") or [],
                            description=entry.get("description") or "",
                            thumbnail_url=entry.get("thumbnail"),
                            has_captions=bool(entry.get("subtitles") or entry.get("automatic_captions")),
                        )
                    )
        except Exception as e:
            print(f"[VideoScraper] Error during search for '{query}': {e}")

        return results
