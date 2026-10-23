"""
Topic Intelligence & Clustering Engine (Tier 2 - Decision Layer).
Converts individual video observations into thematic topic clusters with aggregate metrics:
- Video Count & Competitor Saturation
- Outlier Frequency & Performance Density
- Dominant Creators & Average Velocity
"""

import re
import statistics
from typing import List, Dict, Any
from collections import defaultdict, Counter
from scraper.models import VideoMetadata


class TopicClusteringEngine:
    @staticmethod
    def cluster_videos(videos: List[Dict[str, Any]], min_cluster_size: int = 2) -> List[Dict[str, Any]]:
        """
        Groups a list of analyzed video dictionaries into thematic topic clusters.
        """
        if not videos:
            return []

        # Stop words to ignore during n-gram and keyword extraction
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "this", "that",
            "it", "you", "your", "my", "how", "what", "why", "video", "shorts",
            "channel", "new", "top", "best", "2024", "2025", "2026", "part", "ep",
        }

        # 1. Extract candidate topic phrases (bi-grams and tri-grams from titles)
        phrase_to_videos = defaultdict(list)
        for idx, v in enumerate(videos):
            title = v.get("title", "")
            clean_title = re.sub(r"[^a-zA-Z0-9\s]", " ", title.lower())
            words = [w for w in clean_title.split() if len(w) > 2 and w not in stop_words]

            # Bi-grams
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                phrase_to_videos[phrase].append(idx)

            # Tri-grams
            for i in range(len(words) - 2):
                phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                phrase_to_videos[phrase].append(idx)

        # 2. Filter phrases by frequency threshold
        top_phrases = [
            (phrase, indices) for phrase, indices in phrase_to_videos.items()
            if len(set(indices)) >= min_cluster_size
        ]
        top_phrases.sort(key=lambda x: len(set(x[1])), reverse=True)

        assigned_videos = set()
        clusters: List[Dict[str, Any]] = []

        # 3. Form non-overlapping clusters
        for phrase, indices in top_phrases[:12]:
            unique_indices = [i for i in indices if i not in assigned_videos]
            if len(unique_indices) < min_cluster_size:
                continue

            cluster_vids = [videos[i] for i in unique_indices]
            for i in unique_indices:
                assigned_videos.add(i)

            views_list = [v.get("views", 0) for v in cluster_vids if v.get("views", 0) > 0]
            channels = list(set([v.get("channel_title") or v.get("channel_handle") or "Creator" for v in cluster_vids]))
            outliers = [v for v in cluster_vids if v.get("is_outlier") or v.get("age_adjusted_outlier", 1.0) >= 3.0]

            median_v = float(statistics.median(views_list)) if views_list else 0.0
            avg_v = round(float(statistics.mean(views_list)), 1) if views_list else 0.0

            clusters.append({
                "cluster_id": f"cluster_{len(clusters) + 1}",
                "cluster_name": phrase.title(),
                "video_count": len(cluster_vids),
                "competitor_count": len(channels),
                "median_views": median_v,
                "avg_views": avg_v,
                "outlier_count": len(outliers),
                "outlier_ratio_avg": round(sum(v.get("age_adjusted_outlier", 1.0) for v in cluster_vids) / len(cluster_vids), 2),
                "dominant_creators": channels[:4],
                "sample_videos": [
                    {
                        "title": v.get("title"),
                        "views": v.get("views"),
                        "outlier_ratio": v.get("age_adjusted_outlier", 1.0),
                        "url": v.get("url"),
                    }
                    for v in cluster_vids[:3]
                ],
            })

        # 4. Catch-all general cluster if some videos remained unassigned
        remaining_indices = [i for i in range(len(videos)) if i not in assigned_videos]
        if remaining_indices and len(clusters) < 8:
            rem_vids = [videos[i] for i in remaining_indices]
            views_list = [v.get("views", 0) for v in rem_vids if v.get("views", 0) > 0]
            outliers = [v for v in rem_vids if v.get("is_outlier") or v.get("age_adjusted_outlier", 1.0) >= 3.0]
            
            clusters.append({
                "cluster_id": f"cluster_niche_general",
                "cluster_name": "General Niche Opportunities",
                "video_count": len(rem_vids),
                "competitor_count": len(set([v.get("channel_title") or "Creator" for v in rem_vids])),
                "median_views": float(statistics.median(views_list)) if views_list else 0.0,
                "avg_views": round(float(statistics.mean(views_list)), 1) if views_list else 0.0,
                "outlier_count": len(outliers),
                "outlier_ratio_avg": round(sum(v.get("age_adjusted_outlier", 1.0) for v in rem_vids) / len(rem_vids), 2) if rem_vids else 1.0,
                "dominant_creators": list(set([v.get("channel_title") or "Creator" for v in rem_vids]))[:4],
                "sample_videos": [
                    {
                        "title": v.get("title"),
                        "views": v.get("views"),
                        "outlier_ratio": v.get("age_adjusted_outlier", 1.0),
                        "url": v.get("url"),
                    }
                    for v in rem_vids[:3]
                ],
            })

        return clusters
