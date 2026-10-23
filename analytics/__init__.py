"""
Analytics module exports for VidIQ-style metrics and scoring.
"""

from .metrics import (
    calculate_video_age_hours,
    calculate_view_velocity,
    calculate_engagement_rate,
    calculate_channel_baseline,
    calculate_outlier_score,
    calculate_video_features,
    calculate_age_normalized_outlier,
    calculate_expected_views_for_age,
    get_age_cohort,
    AGE_COHORTS,
)
from .seo_scorer import SEOReadinessEvaluator, SEOScorer
from .keyword_analyzer import KeywordAnalyzer
from .scoring_engine import (
    score_keyword,
    score_title,
    score_content,
    score_channel,
    outlier_multiplier,
    KeywordSignals,
    ResultVideo,
    VideoRec,
    RUBRIC_VERSION,
)

__all__ = [
    "calculate_video_age_hours",
    "calculate_view_velocity",
    "calculate_engagement_rate",
    "calculate_channel_baseline",
    "calculate_outlier_score",
    "calculate_video_features",
    "calculate_age_normalized_outlier",
    "calculate_expected_views_for_age",
    "get_age_cohort",
    "AGE_COHORTS",
    "SEOReadinessEvaluator",
    "SEOScorer",
    "KeywordAnalyzer",
    "score_keyword",
    "score_title",
    "score_content",
    "score_channel",
    "outlier_multiplier",
    "KeywordSignals",
    "ResultVideo",
    "VideoRec",
    "RUBRIC_VERSION",
]
