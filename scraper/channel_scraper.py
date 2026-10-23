"""
Channel Scraper Engine using yt-dlp and direct YouTube Web scraping.
Extracts channel metadata (subscribers, total views, video count, joined date, country)
and recent uploads (Shorts and long-form) for deep algorithmic auditing.
"""

from typing import List, Optional, Dict, Any
import urllib.request
import re
import json
import yt_dlp

from .models import ChannelInfo, ChannelVideoSummary


def parse_count_string(text: Optional[str]) -> Optional[int]:
    """
    Parses count strings like '142 subscribers', '50,562 views', '1.2M subscribers', '45.3K views' into integers.
    """
    if not text:
        return None
    # Remove text like 'subscribers', 'views', 'videos'
    clean = re.sub(r'(?i)(subscribers|subscriber|views|view|videos|video)', '', text).strip()
    clean = clean.replace(',', '').strip()
    
    if not clean:
        return None

    multiplier = 1
    if clean.upper().endswith('B'):
        multiplier = 1_000_000_000
        clean = clean[:-1]
    elif clean.upper().endswith('M'):
        multiplier = 1_000_000
        clean = clean[:-1]
    elif clean.upper().endswith('K'):
        multiplier = 1_000
        clean = clean[:-1]

    try:
        return int(float(clean) * multiplier)
    except Exception:
        return None


class ChannelScraper:
    def __init__(self):
        pass

    @staticmethod
    def normalize_channel_url(identifier: str) -> str:
        """
        Normalizes handles, URLs, and IDs into standard clean root YouTube URLs.
        """
        clean = identifier.strip()
        if clean.startswith("http://") or clean.startswith("https://"):
            url = clean
        elif clean.startswith("www."):
            url = f"https://{clean}"
        elif clean.startswith("youtube.com"):
            url = f"https://{clean}"
        elif clean.startswith("@"):
            url = f"https://www.youtube.com/{clean}"
        elif clean.startswith("UC") and len(clean) == 24:
            url = f"https://www.youtube.com/channel/{clean}"
        else:
            url = f"https://www.youtube.com/@{clean}"

        # Clean trailing subpaths
        root = url.rstrip("/").replace("/videos", "").replace("/shorts", "").replace("/featured", "").replace("/about", "")
        return root

    def get_channel_metadata(self, channel_identifier: str) -> Dict[str, Any]:
        """
        Extracts rich channel metadata including total views, subscriber count, total video count,
        country, joined date, and description from YouTube about/web data.
        """
        root_url = self.normalize_channel_url(channel_identifier)
        metadata: Dict[str, Any] = {
            "channel_name": channel_identifier,
            "channel_id": None,
            "canonical_url": root_url,
            "subscriber_count": None,
            "subscriber_count_text": None,
            "total_views": None,
            "total_views_text": None,
            "video_count": None,
            "video_count_text": None,
            "country": None,
            "joined_date": None,
            "description": None,
        }

        # 1. Scrape YouTube web about endpoint
        about_urls = [f"{root_url}/about", root_url]
        for url in about_urls:
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept-Language": "en-US,en;q=0.9",
                    }
                )
                html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='ignore')
                
                # Parse ytInitialData JSON
                match = re.search(r'var ytInitialData\s*=\s*({.+?});</script>', html)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        
                        def find_about_vm(d):
                            if isinstance(d, dict):
                                if "aboutChannelViewModel" in d:
                                    return d["aboutChannelViewModel"]
                                for v in d.values():
                                    res = find_about_vm(v)
                                    if res:
                                        return res
                            elif isinstance(d, list):
                                for item in d:
                                    res = find_about_vm(item)
                                    if res:
                                        return res
                            return None

                        vm = find_about_vm(data)
                        if vm:
                            if vm.get("subscriberCountText"):
                                metadata["subscriber_count_text"] = vm.get("subscriberCountText")
                                metadata["subscriber_count"] = parse_count_string(vm.get("subscriberCountText"))
                            if vm.get("viewCountText"):
                                metadata["total_views_text"] = vm.get("viewCountText")
                                metadata["total_views"] = parse_count_string(vm.get("viewCountText"))
                            if vm.get("videoCountText"):
                                metadata["video_count_text"] = vm.get("videoCountText")
                                metadata["video_count"] = parse_count_string(vm.get("videoCountText"))
                            if vm.get("country"):
                                metadata["country"] = vm.get("country")
                            if vm.get("joinedDateText", {}).get("content"):
                                metadata["joined_date"] = vm.get("joinedDateText", {}).get("content")
                            if vm.get("description"):
                                metadata["description"] = vm.get("description")
                            if vm.get("channelId"):
                                metadata["channel_id"] = vm.get("channelId")
                            if vm.get("canonicalChannelUrl"):
                                metadata["canonical_url"] = vm.get("canonicalChannelUrl")
                            break
                    except Exception:
                        pass
            except Exception:
                pass

        # 2. Fallback / supplement with yt-dlp info
        try:
            ydl_opts = {
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "playlistend": 1,
                "ignoreerrors": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(root_url, download=False)
                if info:
                    metadata["channel_name"] = info.get("channel") or info.get("uploader") or info.get("title") or metadata["channel_name"]
                    if not metadata["subscriber_count"] and info.get("channel_follower_count"):
                        metadata["subscriber_count"] = info.get("channel_follower_count")
                        metadata["subscriber_count_text"] = f"{info.get('channel_follower_count'):,} subscribers"
                    if not metadata["channel_id"] and info.get("channel_id"):
                        metadata["channel_id"] = info.get("channel_id")
        except Exception:
            pass

        return metadata

    def fetch_channel_videos(
        self, channel_identifier: str, limit: int = 30
    ) -> List[ChannelVideoSummary]:
        """
        Fetches the recent videos list for a channel using yt-dlp flat extraction.
        """
        root_url = self.normalize_channel_url(channel_identifier)
        results: List[ChannelVideoSummary] = []
        seen_ids = set()

        candidate_urls = [
            f"{root_url}/shorts",
            f"{root_url}/videos",
            root_url,
        ]

        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlistend": limit,
            "ignoreerrors": True,
        }

        # Try scraping candidate tabs (shorts & videos)
        for target_url in candidate_urls:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(target_url, download=False)
                    if not info or "entries" not in info or not info["entries"]:
                        continue

                    for item in info["entries"]:
                        if not item:
                            continue
                        v_id = item.get("id")
                        if not v_id or v_id in seen_ids:
                            continue

                        seen_ids.add(v_id)
                        duration_sec = item.get("duration") or 0
                        duration_text = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}" if duration_sec else None

                        results.append(
                            ChannelVideoSummary(
                                video_id=v_id,
                                url=f"https://www.youtube.com/watch?v={v_id}",
                                title=item.get("title", ""),
                                views=item.get("view_count") or 0,
                                published_time_text=item.get("upload_date"),
                                duration_text=duration_text,
                            )
                        )
                    if len(results) >= limit:
                        break
            except Exception:
                pass

        # Fallback: if candidate URLs yielded 0 videos, search YouTube for the channel
        if not results:
            try:
                search_query = f"ytsearch{limit}:{channel_identifier.strip()}"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    s_info = ydl.extract_info(search_query, download=False)
                    if s_info and "entries" in s_info:
                        for item in s_info["entries"]:
                            if item and item.get("id") and item["id"] not in seen_ids:
                                v_id = item["id"]
                                seen_ids.add(v_id)
                                duration_sec = item.get("duration") or 0
                                duration_text = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}" if duration_sec else None
                                results.append(
                                    ChannelVideoSummary(
                                        video_id=v_id,
                                        url=f"https://www.youtube.com/watch?v={v_id}",
                                        title=item.get("title", ""),
                                        views=item.get("view_count") or 0,
                                        published_time_text=item.get("upload_date"),
                                        duration_text=duration_text,
                                    )
                                )
            except Exception:
                pass

        return results[:limit]

    def _fetch_channel_info_api(self, channel_identifier: str, max_videos: int = 30) -> Optional[ChannelInfo]:
        """
        Fetches channel details and recent videos via YouTube Data API v3 if API key is configured.
        """
        import os
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None

        clean_id = channel_identifier.strip()
        channel_id = None

        try:
            # 1. Check if identifier is already channel ID (UC...)
            if clean_id.startswith("UC") and len(clean_id) == 24:
                channel_id = clean_id
            # 2. Check if handle starting with @
            elif clean_id.startswith("@"):
                handle_q = clean_id.lstrip("@")
                r_h = requests.get("https://www.googleapis.com/youtube/v3/channels", params={
                    "part": "snippet,contentDetails,statistics",
                    "forHandle": handle_q,
                    "key": api_key
                }, timeout=6).json()
                if r_h.get("items"):
                    channel_id = r_h["items"][0]["id"]
            
            # 3. Otherwise search channel by query
            if not channel_id:
                clean_q = re.sub(r'https?://(www\.)?youtube\.com/(@|channel/)?', '', clean_id).strip()
                r_s = requests.get("https://www.googleapis.com/youtube/v3/search", params={
                    "part": "snippet",
                    "q": clean_q,
                    "type": "channel",
                    "key": api_key,
                    "maxResults": 1
                }, timeout=6).json()
                if r_s.get("items"):
                    channel_id = r_s["items"][0]["id"]["channelId"]

            if not channel_id:
                return None

            # Fetch Channel Details
            r_c = requests.get("https://www.googleapis.com/youtube/v3/channels", params={
                "part": "snippet,contentDetails,statistics",
                "id": channel_id,
                "key": api_key
            }, timeout=6).json()

            if not r_c.get("items"):
                return None

            ch_item = r_c["items"][0]
            snip = ch_item.get("snippet", {})
            stats = ch_item.get("statistics", {})
            cdetails = ch_item.get("contentDetails", {})
            
            uploads_pl_id = cdetails.get("relatedPlaylists", {}).get("uploads")
            videos_list: List[ChannelVideoSummary] = []

            if uploads_pl_id:
                r_pl = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params={
                    "part": "snippet",
                    "playlistId": uploads_pl_id,
                    "maxResults": min(max_videos, 50),
                    "key": api_key
                }, timeout=6).json()

                v_ids = [it["snippet"]["resourceId"]["videoId"] for it in r_pl.get("items", [])]
                
                if v_ids:
                    # Fetch statistics for videos
                    r_vids = requests.get("https://www.googleapis.com/youtube/v3/videos", params={
                        "part": "snippet,statistics,contentDetails",
                        "id": ",".join(v_ids),
                        "key": api_key
                    }, timeout=6).json()

                    for v_item in r_vids.get("items", []):
                        v_snip = v_item.get("snippet", {})
                        v_stats = v_item.get("statistics", {})
                        v_id = v_item.get("id")
                        v_view_cnt = int(v_stats.get("viewCount", 0))
                        
                        # Parse ISO 8601 duration e.g. PT45S, PT1M20S
                        raw_dur = v_item.get("contentDetails", {}).get("duration", "")
                        d_match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', raw_dur)
                        dur_text = "0:45"
                        if d_match:
                            h, m, s = d_match.groups()
                            sec_total = (int(h or 0) * 3600) + (int(m or 0) * 60) + int(s or 0)
                            dur_text = f"{sec_total // 60}:{sec_total % 60:02d}"

                        videos_list.append(ChannelVideoSummary(
                            video_id=v_id,
                            url=f"https://www.youtube.com/watch?v={v_id}",
                            title=v_snip.get("title", ""),
                            views=v_view_cnt,
                            published_time_text=v_snip.get("publishedAt", "")[:10],
                            duration_text=dur_text,
                        ))

            sub_cnt = int(stats.get("subscriberCount", 0)) if stats.get("subscriberCount") else None
            tot_views = int(stats.get("viewCount", 0)) if stats.get("viewCount") else None
            vid_cnt = int(stats.get("videoCount", len(videos_list))) if stats.get("videoCount") else len(videos_list)

            return ChannelInfo(
                channel_id=channel_id,
                channel_name=snip.get("title", channel_identifier),
                channel_url=f"https://www.youtube.com/channel/{channel_id}",
                subscriber_count=sub_cnt,
                subscriber_count_text=f"{sub_cnt:,} subscribers" if sub_cnt is not None else "N/A",
                total_views=tot_views,
                total_views_text=f"{tot_views:,} views" if tot_views is not None else "N/A",
                video_count=vid_cnt,
                video_count_text=f"{vid_cnt:,} videos",
                country=snip.get("country", "Global"),
                joined_date=snip.get("publishedAt", "")[:10],
                description=snip.get("description", ""),
                recent_videos=videos_list
            )
        except Exception:
            return None

    def get_channel_info(self, channel_identifier: str, max_videos: int = 30) -> Optional[ChannelInfo]:
        """
        Fetches channel profile details and its recent video summaries via API first, with fallback to scraping.
        """
        # Try YouTube Data API first if configured
        api_res = self._fetch_channel_info_api(channel_identifier, max_videos=max_videos)
        if api_res and api_res.recent_videos:
            return api_res

        # Fallback to web scraping
        metadata = self.get_channel_metadata(channel_identifier)
        videos = self.fetch_channel_videos(channel_identifier, limit=max_videos)

        return ChannelInfo(
            channel_id=metadata.get("channel_id"),
            channel_name=metadata.get("channel_name", channel_identifier),
            channel_url=metadata.get("canonical_url", self.normalize_channel_url(channel_identifier)),
            subscriber_count=metadata.get("subscriber_count"),
            subscriber_count_text=metadata.get("subscriber_count_text"),
            total_views=metadata.get("total_views"),
            total_views_text=metadata.get("total_views_text"),
            video_count=metadata.get("video_count") or len(videos),
            video_count_text=metadata.get("video_count_text"),
            country=metadata.get("country"),
            joined_date=metadata.get("joined_date"),
            description=metadata.get("description"),
            recent_videos=videos,
        )

