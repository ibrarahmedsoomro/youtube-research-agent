"""
Transcript Scraper Engine using youtube-transcript-api.
Extracts subtitles/captions (auto-generated or manual) for videos without requiring API credentials.
"""

import re
from typing import Optional, List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)

from .models import TranscriptData, TranscriptSegment


class TranscriptScraper:
    def __init__(self):
        self.api = YouTubeTranscriptApi()

    @staticmethod
    def extract_video_id(url_or_id: str) -> str:
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

    def fetch_transcript(
        self, video_url_or_id: str, languages: Optional[List[str]] = None
    ) -> Optional[TranscriptData]:
        """
        Fetches transcript for a video, supporting automatic language fallback.
        """
        video_id = self.extract_video_id(video_url_or_id)
        if not languages:
            languages = ["en", "ur", "hi", "es", "fr", "de"]

        try:
            transcript_list = self.api.list(video_id)
            
            transcript_obj = None
            try:
                transcript_obj = transcript_list.find_transcript(languages)
            except Exception:
                for t in transcript_list:
                    transcript_obj = t
                    break

            if not transcript_obj:
                return None

            raw_snippets = transcript_obj.fetch()
            segments = []
            for item in raw_snippets:
                text = getattr(item, "text", "") or (item.get("text", "") if isinstance(item, dict) else "")
                start = getattr(item, "start", 0.0) or (item.get("start", 0.0) if isinstance(item, dict) else 0.0)
                duration = getattr(item, "duration", 0.0) or (item.get("duration", 0.0) if isinstance(item, dict) else 0.0)
                
                cleaned_text = str(text).replace("\n", " ").strip()
                if cleaned_text:
                    segments.append(
                        TranscriptSegment(
                            text=cleaned_text,
                            start=float(start),
                            duration=float(duration),
                        )
                    )

            full_text = " ".join([s.text for s in segments if s.text])

            return TranscriptData(
                video_id=video_id,
                language=transcript_obj.language_code,
                is_generated=transcript_obj.is_generated,
                segments=segments,
                full_text=full_text,
            )

        except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript):
            return None
        except Exception as e:
            print(f"[TranscriptScraper] Error for {video_id}: {e}")
            return None

    # Alias for method name consistency
    get_transcript = fetch_transcript
