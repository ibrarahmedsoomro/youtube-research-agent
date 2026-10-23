"""
Data models for the YouTube Research Agent Scraper module.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    video_id: str
    url: str
    title: str
    channel_name: str
    channel_id: Optional[str] = None
    channel_url: Optional[str] = None
    subscriber_count: Optional[int] = None
    views: int = 0
    likes: Optional[int] = 0
    comment_count: Optional[int] = 0
    upload_date: Optional[str] = None  # YYYYMMDD or YYYY-MM-DD
    timestamp: Optional[int] = None    # Unix epoch seconds
    duration_seconds: Optional[int] = 0
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    description: Optional[str] = ""
    thumbnail_url: Optional[str] = None
    has_captions: bool = False


class ChannelVideoSummary(BaseModel):
    video_id: str
    url: str
    title: str
    views: Optional[int] = 0
    published_time_text: Optional[str] = None
    duration_text: Optional[str] = None


class ChannelInfo(BaseModel):
    channel_id: Optional[str] = None
    channel_name: str
    channel_url: str
    custom_url: Optional[str] = None
    subscriber_count: Optional[int] = None
    subscriber_count_text: Optional[str] = None
    total_views: Optional[int] = None
    total_views_text: Optional[str] = None
    video_count: Optional[int] = None
    video_count_text: Optional[str] = None
    country: Optional[str] = None
    joined_date: Optional[str] = None
    description: Optional[str] = None
    recent_videos: List[ChannelVideoSummary] = Field(default_factory=list)


class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float


class TranscriptData(BaseModel):
    video_id: str
    language: str = "en"
    is_generated: bool = True
    segments: List[TranscriptSegment] = Field(default_factory=list)
    full_text: str = ""


# Backwards compatibility & clear alias
VideoTranscript = TranscriptData
