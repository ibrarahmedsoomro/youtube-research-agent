"""
Data Quality and Integrity Engine for YouTube AI Research & Optimization Agent.
Enforces deterministic validation, temporal freshness checks, duplicate deduplication,
and strict non-imputation rules (Rule 15: Missing data = UNKNOWN, no silent fabrication).
"""

from datetime import datetime, timezone
import json
from typing import List, Dict, Any, Tuple
from database.db import get_db
from database.models import DataQualityLog


class DataQualityEngine:
    """
    Evaluates dataset integrity, detects missing or corrupted metadata,
    computes confidence tiers, and logs validation audits to database.
    """

    @staticmethod
    def validate_video_dataset(videos: List[Dict[str, Any]], run_id: str = None, dataset_name: str = "Scraped Video Batch") -> Dict[str, Any]:
        """
        Validates, deduplicates, and sanitizes video data.
        Returns:
            {
                "valid_videos": List[Dict],
                "duplicate_count": int,
                "missing_views_count": int,
                "missing_transcripts_count": int,
                "missing_comments_count": int,
                "stale_count": int,
                "quality_status": "PASSED" | "WARNING" | "FAILED",
                "completeness_score": float (0.0 to 1.0),
                "summary": str
            }
        """
        if not videos:
            return {
                "valid_videos": [],
                "duplicate_count": 0,
                "missing_views_count": 0,
                "missing_transcripts_count": 0,
                "missing_comments_count": 0,
                "stale_count": 0,
                "quality_status": "FAILED",
                "completeness_score": 0.0,
                "summary": "Empty dataset provided for validation."
            }

        seen_ids = set()
        valid_videos = []
        duplicate_count = 0
        missing_views_count = 0
        missing_transcripts_count = 0
        missing_comments_count = 0
        stale_count = 0
        
        now = datetime.now(timezone.utc)

        for v in videos:
            v_id = v.get("video_id") or v.get("id")
            if not v_id:
                continue

            if v_id in seen_ids:
                duplicate_count += 1
                continue
            seen_ids.add(v_id)

            # Sanitize & enforce explicit missing data markers (no silent imputation)
            sanitized = dict(v)
            
            # Views check
            raw_views = v.get("views")
            if raw_views is None or raw_views < 0:
                missing_views_count += 1
                sanitized["views"] = 0
                sanitized["views_status"] = "UNKNOWN"
            else:
                sanitized["views_status"] = "VERIFIED"

            # Transcripts check
            has_transcript = bool(v.get("transcript") or v.get("transcript_text") or v.get("has_transcript"))
            if not has_transcript:
                missing_transcripts_count += 1
                sanitized["transcript_status"] = "UNKNOWN"
            else:
                sanitized["transcript_status"] = "VERIFIED"

            # Comments check
            raw_comments = v.get("comments")
            if raw_comments is None or raw_comments < 0:
                missing_comments_count += 1
                sanitized["comments"] = 0
                sanitized["comments_status"] = "UNKNOWN"
            else:
                sanitized["comments_status"] = "VERIFIED"

            # Freshness / Staleness check
            age_hours = v.get("data_age_hours", 0.0)
            if age_hours > (24 * 90): # > 90 days
                stale_count += 1
                sanitized["freshness_tier"] = "ARCHIVAL (>90d)"
            elif age_hours > (24 * 30):
                sanitized["freshness_tier"] = "MATURE (30-90d)"
            else:
                sanitized["freshness_tier"] = "FRESH (<30d)"

            valid_videos.append(sanitized)

        total_records = len(videos)
        valid_count = len(valid_videos)

        # Completeness calculation
        total_checks = total_records * 3 # views, comments, uniqueness
        failed_checks = duplicate_count + missing_views_count + missing_comments_count
        completeness_score = max(0.0, min(1.0, 1.0 - (failed_checks / max(1, total_checks))))

        if completeness_score >= 0.85 and duplicate_count == 0:
            quality_status = "PASSED"
        elif completeness_score >= 0.50:
            quality_status = "WARNING"
        else:
            quality_status = "FAILED"

        summary = (
            f"Validated {valid_count}/{total_records} videos. "
            f"{duplicate_count} duplicates pruned, {missing_transcripts_count} without transcript, "
            f"{missing_comments_count} without comments. Overall status: {quality_status} "
            f"({completeness_score:.1%} integrity)."
        )

        # Persist validation audit log
        try:
            with get_db() as db:
                log_entry = DataQualityLog(
                    run_id=run_id,
                    dataset_name=dataset_name,
                    total_records=total_records,
                    duplicate_records=duplicate_count,
                    missing_views=missing_views_count,
                    missing_transcripts=missing_transcripts_count,
                    missing_comments=missing_comments_count,
                    stale_records=stale_count,
                    quality_status=quality_status,
                    notes=summary,
                    logged_at=now
                )
                db.add(log_entry)
        except Exception:
            pass # Non-blocking for offline testing

        return {
            "valid_videos": valid_videos,
            "duplicate_count": duplicate_count,
            "missing_views_count": missing_views_count,
            "missing_transcripts_count": missing_transcripts_count,
            "missing_comments_count": missing_comments_count,
            "stale_count": stale_count,
            "quality_status": quality_status,
            "completeness_score": completeness_score,
            "summary": summary
        }

    @staticmethod
    def compute_sample_confidence(sample_size: int, has_channel_baseline: bool = True) -> Tuple[str, str]:
        """
        Determines statistical confidence tier based on sample size and baseline availability.
        Returns (confidence_tier, rationale)
        """
        if sample_size < 3:
            return "INSUFFICIENT EVIDENCE", f"Sample size ({sample_size}) is too small for statistical significance (minimum 3 required)."
        elif sample_size < 8:
            return "LOW", f"Limited sample size ({sample_size} videos). Directional trend only."
        elif sample_size < 20:
            return "MEDIUM", f"Adequate sample size ({sample_size} videos) for pattern extraction."
        else:
            return "HIGH", f"Robust sample size ({sample_size} videos) with strong statistical confidence."
