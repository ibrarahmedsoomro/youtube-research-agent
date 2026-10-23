"""
VidIQ-style Keyword Analyzer & Opportunity Scorer.
Computes Search Demand, Competition Level, Overall Opportunity Score (0 - 100),
and extracts top recurring tags & keywords across ranking videos.
"""

from typing import List, Dict, Any
from collections import Counter
from scraper.models import VideoMetadata
from .metrics import calculate_view_velocity, calculate_video_age_hours


class KeywordAnalyzer:
    @staticmethod
    def analyze_keyword_niche(query: str, search_results: List[VideoMetadata]) -> Dict[str, Any]:
        """
        Analyzes search results for a keyword and outputs:
        - Search Demand Score (0-100)
        - Competition Score (0-100)
        - Opportunity Score (0-100)
        - Common tags & ranking channels
        """
        if not search_results:
            return {
                "query": query,
                "demand_score": 0,
                "competition_score": 0,
                "opportunity_score": 0,
                "verdict": "Insufficient data",
                "top_tags": [],
            }

        total_views = sum(v.views for v in search_results)
        avg_views = total_views / len(search_results)
        
        # Calculate velocity across ranking videos
        velocities = []
        for v in search_results:
            age = calculate_video_age_hours(upload_date=v.upload_date, timestamp=v.timestamp)
            vel = calculate_view_velocity(v.views, age)
            velocities.append(vel["vph"])

        avg_vph = sum(velocities) / len(velocities) if velocities else 0.0

        # -------------------------------------------------------------
        # 1. Search Demand Score (0 - 100)
        # Based on average views and real-time velocity
        # -------------------------------------------------------------
        # e.g., 500k+ avg views = ~100; 100k = ~80; 10k = ~50
        if avg_views > 1_000_000:
            view_demand = 100
        elif avg_views > 500_000:
            view_demand = 85
        elif avg_views > 100_000:
            view_demand = 70
        elif avg_views > 20_000:
            view_demand = 50
        elif avg_views > 5_000:
            view_demand = 35
        else:
            view_demand = 20

        # Velocity booster (if videos are actively gaining views right now)
        velocity_boost = min(int(avg_vph / 50.0), 20)
        demand_score = min(view_demand + velocity_boost, 100)

        # -------------------------------------------------------------
        # 2. Competition Score (0 - 100)
        # Based on channel sizes and ranking barrier
        # -------------------------------------------------------------
        sub_counts = [v.subscriber_count for v in search_results if v.subscriber_count and v.subscriber_count > 0]
        if sub_counts:
            avg_subs = sum(sub_counts) / len(sub_counts)
        else:
            # Fallback estimation based on average views
            avg_subs = avg_views * 2.5

        if avg_subs > 2_000_000:
            competition_score = 95  # Dominated by megastars
        elif avg_subs > 500_000:
            competition_score = 80  # Hard for beginners
        elif avg_subs > 100_000:
            competition_score = 60  # Medium competition
        elif avg_subs > 25_000:
            competition_score = 40  # Low competition
        else:
            competition_score = 20  # Very low competition

        # -------------------------------------------------------------
        # 3. Overall Opportunity Score (0 - 100)
        # Formula: High demand + Low competition = High Score
        # -------------------------------------------------------------
        # Demand (55% weight) + Inverted Competition (45% weight)
        inverted_comp = 100 - competition_score
        opportunity_score = int(round((demand_score * 0.55) + (inverted_comp * 0.45)))
        opportunity_score = max(5, min(opportunity_score, 99))

        if opportunity_score >= 70:
            verdict = "Very High Opportunity 🟢 (Great topic to target!)"
        elif opportunity_score >= 55:
            verdict = "Good Opportunity 🟡 (Solid potential with good thumbnail/hook)"
        elif opportunity_score >= 40:
            verdict = "Medium / Competitive 🟠 (Requires high production & authority)"
        else:
            verdict = "High Competition / Saturated 🔴 (Tough for new channels)"

        # -------------------------------------------------------------
        # 4. Extract recurring top tags & keywords
        # -------------------------------------------------------------
        all_tags = []
        for v in search_results:
            all_tags.extend([t.lower().strip() for t in v.tags if len(t.strip()) > 2])

        top_tags_counter = Counter(all_tags)
        top_tags = [
            {"tag": tag, "frequency": count, "relevance_pct": int(round((count / len(search_results)) * 100))}
            for tag, count in top_tags_counter.most_common(12)
        ]

        return {
            "query": query,
            "sample_size": len(search_results),
            "avg_views": int(avg_views),
            "avg_vph": round(avg_vph, 1),
            "demand_score": demand_score,
            "competition_score": competition_score,
            "opportunity_score": opportunity_score,
            "verdict": verdict,
            "top_tags": top_tags,
        }
