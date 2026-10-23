"""
SEO Readiness & Search-Intent Alignment Evaluator (Tier 2 - Decision Layer).
Transparent heuristic evaluation of metadata readiness for search indexation and CTR.
Explicitly avoids fake/opaque 100-point scores by using defensible criteria ratings:
HIGH READINESS | MODERATE READINESS | LOW READINESS.
"""

import re
from typing import Dict, Any, List, Optional
from scraper.models import VideoMetadata


class SEOReadinessEvaluator:
    @staticmethod
    def evaluate_video(metadata: VideoMetadata, target_query: str = "") -> Dict[str, Any]:
        """
        Evaluates search readiness, query alignment, and indexability heuristics.
        """
        title = (metadata.title or "").strip()
        tags = metadata.tags or []
        desc = (metadata.description or "").strip()
        query = target_query.strip().lower()

        dimensions: List[Dict[str, Any]] = []
        actionable_gaps: List[str] = []
        passed_count = 0
        total_dimensions = 6

        # -------------------------------------------------------------
        # 1. Search-Intent & Query Alignment
        # -------------------------------------------------------------
        intent_type = "Informational"
        title_lower = title.lower()
        if any(w in title_lower for w in ["how to", "tutorial", "guide", "step by step", "tips"]):
            intent_type = "How-To / Educational"
        elif any(w in title_lower for w in ["why", "what happened", "truth about", "explained", "mystery", "exposed"]):
            intent_type = "Investigative / Deep-Dive"
        elif any(w in title_lower for w in ["vs", "review", "worth it", "comparison", "best"]):
            intent_type = "Comparative / Evaluation"
        elif any(w in title_lower for w in ["reaction", "story", "gameplay", "vlog", "challenge"]):
            intent_type = "Entertainment / Narrative"

        query_match = False
        if query:
            query_tokens = [w for w in query.split() if len(w) > 2]
            matched_tokens = [t for t in query_tokens if t in title_lower or t in desc.lower()]
            query_match = len(matched_tokens) >= max(1, len(query_tokens) // 2)
            dim_1_status = "PASS" if query_match else "WARN"
            dim_1_detail = f"Aligned with intent '{intent_type}' ({len(matched_tokens)}/{len(query_tokens)} query terms matched)."
        else:
            dim_1_status = "PASS"
            dim_1_detail = f"Identified search intent: '{intent_type}'."

        if dim_1_status == "PASS":
            passed_count += 1
        else:
            actionable_gaps.append(f"Target query terms '{query}' are not clearly present in the title or primary description.")

        dimensions.append({
            "dimension": "Search-Intent Alignment",
            "status": dim_1_status,
            "intent_category": intent_type,
            "detail": dim_1_detail,
        })

        # -------------------------------------------------------------
        # 2. Title Keyword Prominence (First 40 chars)
        # -------------------------------------------------------------
        title_len = len(title)
        first_40 = title[:40].lower()
        has_primary_hook = bool(re.search(r"[a-z0-9]{3,}", first_40))
        optimal_length = 35 <= title_len <= 75

        if optimal_length and has_primary_hook:
            dim_2_status = "PASS"
            dim_2_detail = f"{title_len} chars (within mobile-safe range with early keyword placement)."
            passed_count += 1
        elif 20 <= title_len <= 95:
            dim_2_status = "WARN"
            dim_2_detail = f"{title_len} chars (acceptable, but optimal readability is 40-70 chars)."
            actionable_gaps.append("Shorten title to under 65 chars to avoid truncation on mobile search cards.")
        else:
            dim_2_status = "FAIL"
            dim_2_detail = f"{title_len} chars (too short for search clarity or excessively truncated)."
            actionable_gaps.append("Rewrite title to 45-65 characters with the primary subject in the first 40 characters.")

        dimensions.append({
            "dimension": "Title Length & Front-Loaded Keywords",
            "status": dim_2_status,
            "detail": dim_2_detail,
        })

        # -------------------------------------------------------------
        # 3. Description Search Snippet (First 150 characters)
        # -------------------------------------------------------------
        first_150 = desc[:150].strip()
        desc_words = len(desc.split())

        if len(first_150) >= 50 and desc_words >= 25:
            dim_3_status = "PASS"
            dim_3_detail = f"Rich overview ({desc_words} words) with clear search snippet opening."
            passed_count += 1
        elif desc_words >= 15:
            dim_3_status = "WARN"
            dim_3_detail = f"Moderate overview ({desc_words} words). Opening snippet can be more descriptive."
            actionable_gaps.append("Expand the first 2 sentences of the description to summarize what viewers learn.")
        else:
            dim_3_status = "FAIL"
            dim_3_detail = f"Sparse description ({desc_words} words). Hinders search crawler contextualization."
            actionable_gaps.append("Write a detailed 2-paragraph overview (100+ words) explaining the video topic.")

        dimensions.append({
            "dimension": "Description Context & Search Snippet",
            "status": dim_3_status,
            "detail": dim_3_detail,
        })

        # -------------------------------------------------------------
        # 4. Tag Cluster Coherence & Specificity
        # -------------------------------------------------------------
        tag_count = len(tags)
        total_tag_chars = sum(len(t) for t in tags)
        title_tokens = set(re.findall(r"\w{4,}", title.lower()))
        tag_tokens = set(re.findall(r"\w{4,}", " ".join(tags).lower()))
        keyword_overlap = title_tokens.intersection(tag_tokens)

        if 5 <= tag_count <= 35 and len(keyword_overlap) >= 1 and total_tag_chars >= 60:
            dim_4_status = "PASS"
            dim_4_detail = f"{tag_count} coherent tags with matching key terms: {', '.join(list(keyword_overlap)[:3])}."
            passed_count += 1
        elif tag_count >= 3:
            dim_4_status = "WARN"
            dim_4_detail = f"{tag_count} tags with limited keyword synergy to the title."
            actionable_gaps.append("Ensure your exact primary title keywords are included as individual tags.")
        else:
            dim_4_status = "FAIL"
            dim_4_detail = f"Only {tag_count} tags. Under-utilized metadata capacity."
            actionable_gaps.append("Add 12-20 relevant tags including primary topic, niche, and long-tail variants.")

        dimensions.append({
            "dimension": "Tag Cluster Coherence",
            "status": dim_4_status,
            "detail": dim_4_detail,
        })

        # -------------------------------------------------------------
        # 5. Chapter / Timestamps Structure
        # -------------------------------------------------------------
        has_timestamps = bool(re.search(r"\b\d{1,2}:\d{2}\b", desc))
        if has_timestamps:
            dim_5_status = "PASS"
            dim_5_detail = "Video chapters / timestamps detected (enables Google Key Moments indexation)."
            passed_count += 1
        else:
            dim_5_status = "WARN"
            dim_5_detail = "No timestamps found in description."
            actionable_gaps.append("Add timestamped chapters (e.g., 0:00 Intro, 1:45 Key Event) to appear in Google Key Moments.")

        dimensions.append({
            "dimension": "Chapter & Key Moments Structure",
            "status": dim_5_status,
            "detail": dim_5_detail,
        })

        # -------------------------------------------------------------
        # 6. Spoken Dialogue / Caption Indexability
        # -------------------------------------------------------------
        if metadata.has_captions:
            dim_6_status = "PASS"
            dim_6_detail = "Subtitles/captions available for algorithmic search indexing."
            passed_count += 1
        else:
            dim_6_status = "WARN"
            dim_6_detail = "No custom subtitles detected."
            actionable_gaps.append("Upload accurate captions or verify auto-captions to ensure dialogue is indexed by YouTube.")

        dimensions.append({
            "dimension": "Spoken Dialogue / Captions Indexability",
            "status": dim_6_status,
            "detail": dim_6_detail,
        })

        # Overall Readiness Rating
        if passed_count >= 5:
            readiness_rating = "HIGH READINESS"
            readiness_badge = "High Readiness 🟢"
            summary = "Metadata is well-structured, intent-aligned, and optimized for search & suggestion indexing."
        elif passed_count >= 3:
            readiness_rating = "MODERATE READINESS"
            readiness_badge = "Moderate Readiness 🟡"
            summary = "Core metadata present, but key indexability signals (timestamps, tags, or snippet) need refinement."
        else:
            readiness_rating = "LOW READINESS"
            readiness_badge = "Low Readiness 🔴"
            summary = "Significant metadata gaps. Video may struggle to index reliably for target search queries."

        return {
            "readiness_rating": readiness_rating,
            "readiness_badge": readiness_badge,
            "passed_dimensions": f"{passed_count}/{total_dimensions}",
            "summary": summary,
            "intent_category": intent_type,
            "dimensions": dimensions,
            "actionable_gaps": actionable_gaps,
        }


# Backwards compatibility alias
SEOScorer = SEOReadinessEvaluator
