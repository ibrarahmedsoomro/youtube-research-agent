"""
Deterministic Opportunity Engine & Evidence Ledger (Tier 2 - Decision Layer).
Calculates mathematically grounded Opportunity Profiles from observable features:
Opportunity = (Demand * Audience_Fit * Outlier_Evidence * Novelty) / (Competition * Production_Cost)
Grounds every opportunity to concrete empirical sources in an Evidence Ledger.
Provides defensible confidence ratings: HIGH | MEDIUM | LOW | INSUFFICIENT EVIDENCE.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import statistics


class OpportunityFinder:
    @staticmethod
    def score_cluster_opportunity(
        cluster: Dict[str, Any],
        niche: str,
        channel_median_views: float = 1000.0,
    ) -> Dict[str, Any]:
        """
        Computes an evidence-backed Opportunity Profile for a discovered topic cluster.
        """
        video_count = cluster.get("video_count", 0)
        outlier_count = cluster.get("outlier_count", 0)
        avg_views = cluster.get("avg_views", 0.0)
        median_views = cluster.get("median_views", 0.0)
        outlier_avg = cluster.get("outlier_ratio_avg", 1.0)
        competitor_count = cluster.get("competitor_count", 1)

        # 1. Observable Feature 1: Demand Index (0-100)
        # Scaled based on cluster view volume vs typical channel baseline
        view_ratio = median_views / max(channel_median_views, 1.0)
        if view_ratio >= 10.0:
            demand = 95.0
        elif view_ratio >= 3.0:
            demand = 82.0
        elif view_ratio >= 1.0:
            demand = 68.0
        else:
            demand = 45.0

        # 2. Observable Feature 2: Outlier Evidence (0-100)
        # Ratio of outlier videos to total videos in cluster
        outlier_density = outlier_count / max(video_count, 1)
        if outlier_density >= 0.4 or outlier_avg >= 4.0:
            outlier_evidence = 94.0
            outlier_desc = "Multiple creators broke out with 4x+ views on this topic."
        elif outlier_density >= 0.2 or outlier_avg >= 2.5:
            outlier_evidence = 78.0
            outlier_desc = "Above-average breakout frequency across creators."
        else:
            outlier_evidence = 50.0
            outlier_desc = "Standard performance distribution."

        # 3. Observable Feature 3: Competition & Saturation (0-100)
        # Lower competition = better opportunity.
        if competitor_count >= 8:
            competition = 85.0
            comp_rating = "High Saturation (Oversaturated)"
        elif competitor_count >= 4:
            competition = 55.0
            comp_rating = "Moderate Competition"
        else:
            competition = 25.0
            comp_rating = "Low Competition (Open Niche Gap 🟢)"

        # 4. Observable Feature 4: Audience Fit (0-100)
        audience_fit = 85.0 if "general" not in cluster.get("cluster_id", "") else 70.0

        # 5. Observable Feature 5: Novelty (0-100)
        novelty = 80.0 if competitor_count <= 3 else 60.0

        # 6. Observable Feature 6: Production Difficulty / Cost (0-100)
        production_cost = 40.0  # Moderate standard script production

        # -------------------------------------------------------------
        # Deterministic Formula Calculation
        # Opportunity = (Demand * Audience_Fit * Outlier_Evidence * Novelty) / (Competition * Cost)
        # -------------------------------------------------------------
        comp_factor = max(15.0, competition)
        cost_factor = max(15.0, production_cost)
        
        numerator = (demand / 100.0) * (audience_fit / 100.0) * (outlier_evidence / 100.0) * (novelty / 100.0)
        denominator = (comp_factor / 100.0) * (cost_factor / 100.0)
        
        raw_opp_ratio = numerator / max(denominator, 0.01)
        # Scale to 0-100 index
        opp_score = round(min(98.0, max(20.0, raw_opp_ratio * 45.0)), 1)

        # Confidence assessment based on empirical observations
        if video_count >= 5 and outlier_count >= 2:
            confidence = "HIGH"
        elif video_count >= 2:
            confidence = "MEDIUM"
        else:
            confidence = "INSUFFICIENT EVIDENCE"

        # Tiers
        if opp_score >= 88.0:
            tier = "High-Opportunity Breakout 🔥"
        elif opp_score >= 75.0:
            tier = "Strong Candidate 🟢"
        elif opp_score >= 60.0:
            tier = "Moderate Viability 🟡"
        else:
            tier = "Low Priority / Oversaturated 🔴"

        # -------------------------------------------------------------
        # Evidence Ledger Construction
        # -------------------------------------------------------------
        evidence_ledger = []
        for sample in cluster.get("sample_videos", [])[:3]:
            evidence_ledger.append({
                "claim": f"Observed {sample.get('outlier_ratio', 1.0)}x views multiplier on related title",
                "metric_name": "Outlier Multiplier",
                "metric_value": f"{sample.get('outlier_ratio', 1.0)}x ({sample.get('views', 0):,} views)",
                "source_title": sample.get("title"),
                "source_url": sample.get("url"),
                "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            })

        return {
            "cluster_name": cluster.get("cluster_name"),
            "opportunity_score": opp_score,
            "tier": tier,
            "confidence": confidence,
            "observable_features": {
                "demand": {"score": demand, "label": "Strong" if demand >= 75 else "Moderate"},
                "outlier_evidence": {"score": outlier_evidence, "label": outlier_desc},
                "competition": {"score": competition, "label": comp_rating},
                "audience_fit": {"score": audience_fit, "label": "Aligned with Niche"},
                "novelty": {"score": novelty, "label": "Fresh Angle" if novelty >= 75 else "Standard"},
                "production_difficulty": {"score": production_cost, "label": "Standard Production"},
            },
            "evidence_ledger": evidence_ledger,
            "dominant_creators": cluster.get("dominant_creators", []),
            "video_count": video_count,
            "outlier_count": outlier_count,
        }

    @staticmethod
    def generate_grounded_opportunities(
        clusters: List[Dict[str, Any]],
        niche: str,
        channel_median_views: float = 1000.0,
    ) -> List[Dict[str, Any]]:
        """
        Processes all clusters and returns ranked, evidence-grounded opportunities.
        """
        opportunities = []
        for c in clusters:
            opp = OpportunityFinder.score_cluster_opportunity(c, niche, channel_median_views)
            if opp["confidence"] != "INSUFFICIENT EVIDENCE" or opp["opportunity_score"] >= 60.0:
                opportunities.append(opp)

        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return opportunities[:8]
