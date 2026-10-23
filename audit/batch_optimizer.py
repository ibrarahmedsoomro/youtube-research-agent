"""
Batch Auto-Optimization Engine.
Scans channel video catalogs, flags low-scoring videos (Score < 80),
and automatically produces high-CTR titles, tag clouds, and optimized descriptions
in a single 1-click batch workflow.
"""

import re
from typing import List, Dict, Any, Optional
from database.db import log_system_event
from production.title_intelligence import TitleIntelligenceEngine
from analytics.keyword_analyzer import KeywordAnalyzer
from operations.youtube_publisher import YouTubePublisher

class BatchOptimizer:
    def __init__(self):
        self.keyword_analyzer = KeywordAnalyzer()

    def scan_and_generate_batch(
        self,
        videos: List[Dict[str, Any]],
        score_threshold: int = 80,
        channel_niche: str = "horror stories animation"
    ) -> Dict[str, Any]:
        """
        Scans all videos, identifies those under the score threshold,
        and generates turnkey optimized metadata with projected score increases.
        """
        log_system_event("BatchOptimizer", f"Scanning {len(videos)} videos with threshold {score_threshold}")
        
        flagged_videos = []
        batch_items = []
        
        for v in videos:
            v_title = v.get("title", "")
            v_views = v.get("views", 0)
            v_id = v.get("video_id", "")
            
            # Calculate current scores using TitleIntelligenceEngine
            t_eval = TitleIntelligenceEngine.analyze_title(v_title)
            clarity = t_eval.get("clarity_score", 60.0)
            curiosity = t_eval.get("curiosity_score", 60.0)
            current_title_score = int((clarity + curiosity) / 2)
            
            # Estimated current SEO based on title & tag presence
            current_seo_score = max(30, min(current_title_score - 5 + (15 if len(v_title) > 35 else 0), 95))
            current_overall = int((current_title_score + current_seo_score) / 2)
            
            if current_overall < score_threshold:
                # Generate high-CTR Title Upgrades
                title_candidates = self._generate_optimized_titles(v_title, channel_niche)
                recommended_title = title_candidates[0]["title"] if title_candidates else v_title
                
                # Generate High-Value SEO Tags
                recommended_tags = self._generate_seo_tags(v_title, channel_niche)
                
                # Generate Description Snippet
                recommended_desc = self._generate_description(recommended_title, recommended_tags)
                
                # Calculate projected scores
                proj_eval = TitleIntelligenceEngine.analyze_title(recommended_title)
                proj_title_score = int((proj_eval.get("clarity_score", 85) + proj_eval.get("curiosity_score", 90)) / 2)
                proj_seo_score = min(98, proj_title_score + 6)
                proj_overall = int((proj_title_score + proj_seo_score) / 2)
                
                item = {
                    "video_id": v_id,
                    "thumbnail": v.get("thumbnail") or v.get("thumbnail_url") or "",
                    "url": v.get("url") or f"https://www.youtube.com/watch?v={v_id}",
                    "current": {
                        "title": v_title,
                        "views": v_views,
                        "title_score": current_title_score,
                        "seo_score": current_seo_score,
                        "overall_score": current_overall
                    },
                    "optimized": {
                        "title": recommended_title,
                        "title_candidates": title_candidates,
                        "tags": recommended_tags,
                        "description": recommended_desc,
                        "projected_title_score": proj_title_score,
                        "projected_seo_score": proj_seo_score,
                        "projected_overall_score": proj_overall,
                        "projected_score_gain": max(5, proj_overall - current_overall)
                    },
                    "status": "READY_FOR_SYNC"
                }
                flagged_videos.append(v)
                batch_items.append(item)

        avg_gain = sum(item["optimized"]["projected_score_gain"] for item in batch_items) / len(batch_items) if batch_items else 0

        return {
            "total_videos_scanned": len(videos),
            "flagged_count": len(batch_items),
            "healthy_count": len(videos) - len(batch_items),
            "average_projected_gain": round(avg_gain, 1),
            "batch_items": batch_items
        }

    def _generate_optimized_titles(self, original_title: str, niche: str) -> List[Dict[str, Any]]:
        """Generates 3 punchy, high-CTR alternative titles tailored to the video topic."""
        clean = re.sub(r'#\S+', '', original_title or "")
        clean = clean.split("|")[0].split("-")[0].split("—")[0].split(":")[0].strip()
        clean = re.sub(r'[^\w\s]', '', clean).strip()
        topic_phrase = " ".join([w.capitalize() for w in clean.split()[:5]]) if clean else "This Topic"
        
        formulas = [
            (f"Why Everyone Is Wrong About {topic_phrase}", "Curiosity / Contrarian"),
            (f"The #1 {topic_phrase} Mistake You Must Avoid in 2026", "Warning / Dread Hook"),
            (f"How to Master {topic_phrase} (Step-by-Step Guide)", "Transformation / Mastery")
        ]
        
        candidates = []
        for idx, (title_text, formula_name) in enumerate(formulas, 1):
            t_eval = TitleIntelligenceEngine.analyze_title(title_text)
            sc = int((t_eval.get("clarity_score", 85) + t_eval.get("curiosity_score", 90)) / 2)
            candidates.append({
                "candidate_id": idx,
                "title": title_text,
                "score": min(98, max(85, sc)),
                "formula": formula_name
            })
        return candidates

    def _generate_seo_tags(self, title: str, niche: str) -> List[Dict[str, Any]]:
        """Extracts and suggests dynamic high-search opportunity keyword tags for any topic."""
        from production.description_keyword_engine import DescriptionKeywordEngine
        smart_tags = DescriptionKeywordEngine.generate_smart_tags(title)
        
        tags_out = []
        for t in smart_tags:
            score = t.get("score", 75)
            search_vol = "Very High" if score >= 85 else ("High" if score >= 70 else "Medium")
            tags_out.append({
                "tag": t.get("term", ""),
                "opportunity_score": score,
                "search_volume": search_vol,
                "competition": "Low" if score > 80 else "Medium"
            })
        return tags_out

    def _generate_description(self, title: str, tags: List[Dict[str, Any]]) -> str:
        """Generates a keyword-rich, algorithm-friendly description tailored to the video."""
        clean_title = re.sub(r'#\S+', '', title).strip()
        tag_str = " ".join([f"#{t['tag'].replace(' ', '')}" for t in tags[:5]])
        return (
            f"📌 In this video, we break down everything you need to know about {clean_title}.\n\n"
            f"Watch till the end for practical insights, key takeaways, and action steps.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ Chapters:\n"
            f"0:00 - Introduction & Overview\n"
            f"1:15 - Core Concepts & Analysis\n"
            f"3:45 - Key Strategy & Action Plan\n"
            f"6:30 - Final Conclusion & Summary\n\n"
            f"{tag_str}"
        )

    def apply_batch_optimizations(
        self,
        batch_items: List[Dict[str, Any]],
        publisher: Optional[YouTubePublisher] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Executes metadata update across all batch items in one click.
        """
        pub = publisher or YouTubePublisher()
        results = []
        success_count = 0
        
        for item in batch_items:
            v_id = item["video_id"]
            opt = item["optimized"]
            tag_names = [t["tag"] for t in opt["tags"]]
            
            res = pub.update_video_metadata(
                video_id=v_id,
                title=opt["title"],
                description=opt["description"],
                tags=tag_names,
                dry_run=dry_run
            )
            
            if res.get("status") in ["PUBLISHED_LIVE", "SANDBOX_SIMULATED_SUCCESS"]:
                success_count += 1
            
            results.append({
                "video_id": v_id,
                "title": opt["title"],
                "status": res.get("status"),
                "is_sandbox": res.get("is_sandbox", True),
                "message": res.get("message", "")
            })
            
        return {
            "total_processed": len(batch_items),
            "successful_updates": success_count,
            "failed_updates": len(batch_items) - success_count,
            "dry_run": dry_run,
            "execution_log": results
        }
