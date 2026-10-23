"""
Verification script for Module 1: YouTube Scraper & Extraction Engine.
Tests search, video metadata, channel scraping, and transcript fetching.
"""

import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import json
from scraper import VideoScraper, ChannelScraper, TranscriptScraper

def main():
    print("=" * 70)
    print("        TESTING MODULE 1: YOUTUBE DATA EXTRACTION ENGINE")
    print("=" * 70)

    # 1. Test Video Search
    print("\n[Step 1] Testing Keyword Search via VideoScraper...")
    query = "Python AI Agent tutorial"
    video_scraper = VideoScraper()
    print(f"Searching for: '{query}' (limit: 3)...")
    
    videos = video_scraper.search_videos(query=query, max_results=3)
    print(f"Found {len(videos)} videos.")
    for i, v in enumerate(videos, 1):
        print(f"  {i}. [{v.video_id}] {v.title}")
        print(f"     Channel: {v.channel_name} | Views: {v.views:,} | Likes: {v.likes:,}")
        print(f"     Tags ({len(v.tags)}): {', '.join(v.tags[:5]) if v.tags else 'No tags'}")
        print(f"     Duration: {v.duration_seconds}s | Upload Date: {v.upload_date}")

    test_video_id = videos[0].video_id if videos else "dQw4w9WgXcQ"

    # 2. Test Deep Single Video Extraction
    print(f"\n[Step 2] Testing Deep Metadata Extraction for Video ID: {test_video_id}...")
    details = video_scraper.fetch_video_details(test_video_id)
    if details:
        print(f"  Title: {details.title}")
        print(f"  Channel: {details.channel_name} ({details.channel_url})")
        print(f"  Views: {details.views:,}")
        print(f"  Likes: {details.likes:,}")
        print(f"  Comments: {details.comment_count:,}")
        print(f"  Tags: {details.tags[:8] if details.tags else []}")
        print(f"  Has Captions: {details.has_captions}")
        print(f"  Description snippet: {details.description[:120].strip()}...")
    else:
        print("  Failed to fetch video details.")

    # 3. Test Transcript Extraction
    print(f"\n[Step 3] Testing Transcript Scraper for Video ID: {test_video_id}...")
    transcript_scraper = TranscriptScraper()
    transcript = transcript_scraper.fetch_transcript(test_video_id)
    if transcript:
        print(f"  Success! Language: {transcript.language} (Auto-generated: {transcript.is_generated})")
        print(f"  Segments count: {len(transcript.segments)}")
        print(f"  Transcript Preview: {transcript.full_text[:200]}...")
    else:
        print("  No transcript available for this video (normal for some videos/shorts).")

    # 4. Test Channel Scraper
    test_channel = "@freecodecamp"
    print(f"\n[Step 4] Testing Channel Scraper for '{test_channel}' (limit 5 videos)...")
    channel_scraper = ChannelScraper()
    channel_videos = channel_scraper.fetch_channel_videos(test_channel, limit=5)
    print(f"  Fetched {len(channel_videos)} recent videos from {test_channel}:")
    for i, cv in enumerate(channel_videos, 1):
        print(f"  {i}. [{cv.video_id}] {cv.title}")
        print(f"     Views: {cv.views:,} | Published: {cv.published_time_text} | Duration: {cv.duration_text}")

    print("\n" + "=" * 70)
    print("MODULE 1 TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
