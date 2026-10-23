"""
Deterministic Performance & Outlier Engine (Tier 2 - Decision Layer).
Implements:
- Age Cohort Segmentation (0-6h, 6-24h, 1-3d, 3-7d, 7-30d, 30-90d, 90d+)
- 2-Phase View Growth Model:
  1. Initial Launch Burst (0-7 days): E_burst(t) = Median * (1 - e^(-lambda * t))
  2. Long-Tail Evergreen Accumulation (7+ days): E_longtail(t) = E_burst(t) * (1 + beta * ln(1 + (t-168)/168))
- Age-Normalized Outlier Scoring with Sample-Size Confidence
- Multi-Feature Telemetry Extraction (VPH, Views/Sub, Engagement Rates, Cohort Baselines)
"""

import time
import math
import statistics
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union, Tuple

# Configurable Age Cohorts (in hours)
AGE_COHORTS: List[Dict[str, Any]] = [
    {"name": "0-6h", "min_h": 0.0, "max_h": 6.0, "label": "Ultra-Fresh"},
    {"name": "6-24h", "min_h": 6.0, "max_h": 24.0, "label": "Day 1"},
    {"name": "1-3d", "min_h": 24.0, "max_h": 72.0, "label": "Days 1-3"},
    {"name": "3-7d", "min_h": 72.0, "max_h": 168.0, "label": "Week 1"},
    {"name": "7-30d", "min_h": 168.0, "max_h": 720.0, "label": "Month 1"},
    {"name": "30-90d", "min_h": 720.0, "max_h": 2160.0, "label": "Quarter 1"},
    {"name": "90d+", "min_h": 2160.0, "max_h": float("inf"), "label": "Mature/Evergreen"},
]


def parse_datetime_to_timestamp(upload_date: Optional[str], timestamp: Optional[Union[int, float]] = None) -> Optional[float]:
    """
    Normalizes upload date or unix timestamp into an epoch timestamp.
    """
    if timestamp is not None and float(timestamp) > 0:
        return float(timestamp)

    if not upload_date:
        return None

    cleaned = str(upload_date).strip().replace("-", "")
    if len(cleaned) == 8 and cleaned.isdigit():
        try:
            dt = datetime.strptime(cleaned, "%Y%m%d").replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            pass

    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            dt = datetime.strptime(str(upload_date).strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            continue

    return None


def calculate_video_age_hours(upload_date: Optional[str] = None, timestamp: Optional[Union[int, float]] = None) -> float:
    """
    Calculates video age in hours from upload time to current epoch.
    Floor of 0.1 hours prevents division by zero.
    """
    now_ts = time.time()
    epoch = parse_datetime_to_timestamp(upload_date, timestamp)

    if not epoch or epoch > now_ts:
        return 24.0  # Safe default 1 day if timestamp unavailable

    age_hours = (now_ts - epoch) / 3600.0
    return max(age_hours, 0.1)


def get_age_cohort(age_hours: float) -> Dict[str, Any]:
    """
    Assigns a video to its respective age cohort bucket.
    """
    for cohort in AGE_COHORTS:
        if cohort["min_h"] <= age_hours < cohort["max_h"]:
            return cohort
    return AGE_COHORTS[-1]


def calculate_expected_views_for_age(
    channel_median_views: float,
    age_hours: float,
    decay_lambda: float = 0.035,
    evergreen_beta: float = 0.25,
) -> float:
    """
    2-Phase View Growth Model:
    1. Burst Phase (0-7 days / 0-168h):
       E_burst(t) = Channel_Median * (1 - e^(-lambda * t))
    2. Evergreen Long-Tail Phase (7+ days / >168h):
       E_total(t) = E_burst(t) * [1 + beta * ln(1 + (t - 168) / 168)]
       
    This models both:
    - Rapid initial velocity in first 72 hours
    - Gradual continuous search & recommendation accumulation over months/years
    """
    if channel_median_views <= 0:
        return 1.0

    t = max(age_hours, 0.1)
    # 1. Burst Saturation (approaches 1.0 at ~168 hours)
    burst_saturation = 1.0 - math.exp(-decay_lambda * t)
    base_expected = channel_median_views * burst_saturation

    # 2. Evergreen Long-Tail Multiplier (for videos older than 1 week)
    if t > 168.0:
        weeks_beyond_burst = (t - 168.0) / 168.0
        evergreen_growth = 1.0 + (evergreen_beta * math.log(1.0 + weeks_beyond_burst))
        base_expected *= evergreen_growth

    return max(round(base_expected, 1), 1.0)


def calculate_age_normalized_outlier(
    actual_views: int,
    expected_views: float,
    sample_size: int = 10,
) -> Dict[str, Any]:
    """
    Computes the age-adjusted outlier ratio and deterministic classification tier.
    Outlier = Actual Views / Expected Views for Age.
    """
    if expected_views <= 0:
        outlier_ratio = 1.0
    else:
        outlier_ratio = round(actual_views / expected_views, 2)

    if outlier_ratio >= 5.0:
        tier = "EXTREME OUTLIER"
        badge = "Extreme Outlier 🔥"
        description = f"{outlier_ratio}x expected views for age ({actual_views:,} vs {expected_views:,.0f} expected)."
        is_outlier = True
    elif outlier_ratio >= 3.0:
        tier = "STRONG OUTLIER"
        badge = "Strong Outlier 🚀"
        description = f"{outlier_ratio}x expected views for age ({actual_views:,} vs {expected_views:,.0f} expected)."
        is_outlier = True
    elif outlier_ratio >= 1.5:
        tier = "EMERGING"
        badge = "Emerging Performer 📈"
        description = f"{outlier_ratio}x expected views ({actual_views:,} vs {expected_views:,.0f} expected)."
        is_outlier = False
    elif outlier_ratio >= 0.7:
        tier = "NORMAL"
        badge = "Normal Baseline ⚖️"
        description = f"Standard trajectory ({outlier_ratio}x expected views)."
        is_outlier = False
    else:
        tier = "UNDERPERFORMING"
        badge = "Underperforming ❄️"
        description = f"Below baseline expectations ({outlier_ratio}x expected views)."
        is_outlier = False

    # Sample-size based confidence
    if sample_size >= 25:
        confidence = "HIGH"
    elif sample_size >= 8:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "outlier_ratio": outlier_ratio,
        "outlier_multiplier": outlier_ratio,
        "tier": tier,
        "badge": badge,
        "description": description,
        "is_outlier": is_outlier,
        "is_breakout": is_outlier,
        "confidence": confidence,
        "sample_size": sample_size,
    }


def calculate_view_velocity(views: int, age_hours: float) -> Dict[str, Any]:
    """Computes VPH and daily velocity."""
    if age_hours <= 0:
        age_hours = 1.0
    vph = round(views / age_hours, 2)
    views_per_day = round(vph * 24.0, 1)
    return {
        "vph": vph,
        "views_per_day": views_per_day,
        "age_hours": round(age_hours, 1),
        "age_days": round(age_hours / 24.0, 1),
    }


def calculate_engagement_rate(views: int, likes: int = 0, comments: int = 0) -> Dict[str, Any]:
    """Computes standard engagement rates."""
    if views <= 0:
        return {"raw_rate_percent": 0.0, "weighted_score": 0.0, "grade": "N/A"}

    raw_rate = ((likes + comments) / views) * 100.0
    weighted_score = ((likes * 1.0 + comments * 2.5) / views) * 100.0

    if raw_rate >= 6.0:
        grade = "Exceptional 🔥"
    elif raw_rate >= 3.5:
        grade = "High 🟢"
    elif raw_rate >= 1.5:
        grade = "Average 🟡"
    else:
        grade = "Low 🔴"

    return {
        "raw_rate_percent": round(raw_rate, 2),
        "weighted_score": round(weighted_score, 2),
        "grade": grade,
    }


def calculate_outlier_score(video_views: int, channel_median_views: float) -> Dict[str, Any]:
    """Backwards compatibility helper."""
    return calculate_age_normalized_outlier(video_views, max(channel_median_views, 1.0))


def calculate_channel_baseline(views_list: List[int]) -> Dict[str, float]:
    """Computes robust channel metrics using median."""
    valid_views = [v for v in views_list if v > 0]
    if not valid_views:
        return {"median_views": 0.0, "mean_views": 0.0, "min_views": 0.0, "max_views": 0.0, "sample_size": 0}

    return {
        "median_views": float(statistics.median(valid_views)),
        "mean_views": round(float(statistics.mean(valid_views)), 1),
        "min_views": float(min(valid_views)),
        "max_views": float(max(valid_views)),
        "sample_size": len(valid_views),
    }


def calculate_video_features(
    views: int,
    likes: int = 0,
    comments: int = 0,
    age_hours: float = 24.0,
    channel_median_views: float = 1000.0,
    subscriber_count: int = 0,
    cohort_median_views: Optional[float] = None,
    channel_sample_size: int = 10,
) -> Dict[str, Any]:
    """Computes the complete, deterministic multi-feature telemetry vector for a video."""
    safe_age = max(age_hours, 0.1)
    safe_views = max(views, 0)
    cohort = get_age_cohort(safe_age)

    vph = round(safe_views / safe_age, 2)
    vpd = round(vph * 24.0, 1)

    like_rate = round((likes / safe_views * 100.0), 2) if safe_views > 0 else 0.0
    comment_rate = round((comments / safe_views * 100.0), 2) if safe_views > 0 else 0.0
    raw_engagement_rate = round(((likes + comments) / safe_views * 100.0), 2) if safe_views > 0 else 0.0
    weighted_engagement_score = round(((likes * 1.0 + comments * 2.5) / safe_views * 100.0), 2) if safe_views > 0 else 0.0

    views_per_subscriber = round(safe_views / max(subscriber_count, 1), 3) if subscriber_count > 0 else None

    effective_channel_median = max(channel_median_views, 1.0)
    expected_views = calculate_expected_views_for_age(effective_channel_median, safe_age)
    outlier_data = calculate_age_normalized_outlier(safe_views, expected_views, sample_size=channel_sample_size)

    views_vs_cohort = round(safe_views / max(cohort_median_views, 1.0), 2) if cohort_median_views and cohort_median_views > 0 else None
    views_vs_channel_median = round(safe_views / effective_channel_median, 2)

    return {
        "views": safe_views,
        "likes": likes,
        "comments": comments,
        "age_hours": round(safe_age, 1),
        "age_days": round(safe_age / 24.0, 1),
        "cohort": cohort["name"],
        "cohort_label": cohort["label"],
        "views_per_hour": vph,
        "views_per_day": vpd,
        "like_rate_percent": like_rate,
        "comment_rate_percent": comment_rate,
        "engagement_rate_percent": raw_engagement_rate,
        "weighted_engagement_score": weighted_engagement_score,
        "views_per_subscriber": views_per_subscriber,
        "views_vs_channel_median": views_vs_channel_median,
        "views_vs_age_cohort": views_vs_cohort,
        "expected_views_for_age": round(expected_views, 1),
        "age_adjusted_outlier": outlier_data["outlier_ratio"],
        "outlier_tier": outlier_data["tier"],
        "outlier_badge": outlier_data["badge"],
        "outlier_description": outlier_data["description"],
        "is_outlier": outlier_data["is_outlier"],
        "confidence": outlier_data["confidence"],
    }
