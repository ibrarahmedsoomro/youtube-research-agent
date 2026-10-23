"""
Competitor Breakout & Topic Gap Scanner.
Cross-analyzes our channel's catalog against competitor channels to pinpoint
high-velocity outlier topics (>2.0x median) that our channel has not yet covered.
"""

from typing import List, Dict, Any, Optional
import re
from database.db import log_system_event
from competitors.tracker import CompetitorTracker

class CompetitorGapScanner:
    def __init__(self):
        self.tracker = CompetitorTracker()

    def scan_topic_gaps(
        self,
        our_channel_videos: List[Dict[str, Any]],
        competitor_channels: List[str],
        max_videos_per_competitor: int = 15
    ) -> Dict[str, Any]:
        """
        Identifies untapped high-velocity topic opportunities by comparing our catalog
        against competitor breakout videos.
        """
        log_system_event("CompetitorGapScanner", f"Scanning gaps across {len(competitor_channels)} competitors")
        
        # 1. Extract existing keywords from our channel
        our_titles = [v.get("title", "").lower() for v in our_channel_videos]
        our_corpus = " ".join(our_titles)
        
        # 2. Analyze competitors
        comp_results = self.tracker.track_multiple_channels(
            competitor_channels,
            max_videos_per_channel=max_videos_per_competitor
        )
        
        breakouts = comp_results.get("breakout_videos", [])
        
        # 3. Filter for Breakout Topics where we have an content gap
        topic_gaps = []
        
        for b in breakouts:
            title = b.get("title", "")
            channel = b.get("channel", "Competitor")
            multiplier = b.get("outlier_multiplier", 1.0)
            views = b.get("views", 0)
            
            # Extract key 2-word & 3-word n-grams or distinctive nouns
            clean_title = re.sub(r"[^\w\s]", "", title.lower())
            words = [w for w in clean_title.split() if len(w) > 3 and w not in {
                "this", "that", "with", "from", "video", "shorts", "youtube", "full", "what", "watch"
            }]
            
            # Check how frequently these key terms appear in our catalog
            overlap_score = sum(1 for w in words if w in our_corpus)
            is_uncovered = (overlap_score <= 1)
            
            if is_uncovered or multiplier >= 3.0:
                # High-value gap detected
                opportunity_score = min(99, int(70 + (multiplier * 3.5) + (10 if is_uncovered else 0)))
                
                # Turn competitor title into actionable production ideas for our channel
                hook_idea = f"Why Nobody Talks About {words[0].capitalize() if words else 'This Anomaly'}..."
                recommended_title = f"The {words[0].capitalize() if words else 'Dark'} Incident That YouTube Tried To Delete"
                
                topic_gaps.append({
                    "competitor_channel": channel,
                    "competitor_title": title,
                    "competitor_views": views,
                    "outlier_multiplier": multiplier,
                    "coverage_in_our_channel": "Missing (0%)" if overlap_score == 0 else "Low (<20%)",
                    "opportunity_score": opportunity_score,
                    "actionable_title_idea": recommended_title,
                    "target_hook": hook_idea,
                    "recommended_format": "YouTube Shorts (30-45s)" if b.get("duration_text", "") and ":" not in b.get("duration_text", "") else "Shorts / Fast Vertical"
                })

        # Sort gaps by opportunity score descending
        topic_gaps.sort(key=lambda x: x["opportunity_score"], reverse=True)

        return {
            "competitor_count": len(competitor_channels),
            "competitors_analyzed": comp_results.get("channels", []),
            "total_breakouts_inspected": len(breakouts),
            "gaps_found": len(topic_gaps),
            "top_gaps": topic_gaps[:10]
        }
