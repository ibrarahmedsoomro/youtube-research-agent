"""
Pre-Publish Safety & Quality Auditor (Section 22 & 48).
The ultimate quality gatekeeper that checks policy risks, copyright cues,
metadata completeness, and thumbnail text crowding before approving for publish.
"""

from typing import Dict, Any, List
import re
from database.db import get_db, log_system_event
from database.models import Audit, Approval


class PrePublishAuditor:
    @staticmethod
    def audit_pre_publish(
        title: str,
        description: str,
        tags: List[str],
        hook: str,
        script_text: str,
        thumbnail_text: str = "",
        format_type: str = "Shorts",  # Shorts or Long-form
    ) -> Dict[str, Any]:
        """
        Audits all packaging, script, and policy factors prior to human approval or upload.
        """
        log_system_event("PrePublishAuditor", f"Running Pre-Publish Gate for title: {title[:40]}")
        
        score = 100
        problems: List[Dict[str, Any]] = []
        strengths: List[str] = []
        policy_risk = "LOW"
        copyright_risk = "LOW"
        is_blocked = False

        # -------------------------------------------------------------
        # 1. Title Audit
        # -------------------------------------------------------------
        t_len = len(title.strip())
        if 40 <= t_len <= 65:
            strengths.append(f"Title length ({t_len} chars) is perfect for mobile discovery.")
        elif t_len > 70:
            score -= 10
            problems.append({
                "area": "Title",
                "severity": "HIGH",
                "issue": f"Title is {t_len} characters long and will be truncated on mobile.",
                "fix": "Trim title to 45–65 characters.",
            })
        elif t_len < 25:
            score -= 12
            problems.append({
                "area": "Title",
                "severity": "HIGH",
                "issue": "Title is too short to establish strong curiosity or context.",
                "fix": "Expand title with emotional hooks, brackets, or numbers.",
            })

        # -------------------------------------------------------------
        # 2. Thumbnail Text Overcrowding (Max 4 words rule)
        # -------------------------------------------------------------
        thumb_words = thumbnail_text.strip().split()
        if len(thumb_words) > 4:
            score -= 15
            problems.append({
                "area": "Thumbnail",
                "severity": "HIGH",
                "issue": f"Thumbnail has {len(thumb_words)} words ('{thumbnail_text}'). Too crowded for 0.5s mobile scan.",
                "fix": "Reduce thumbnail text to 2–4 high-impact words (e.g., 'DON'T DO THIS!').",
            })
        elif thumb_words:
            strengths.append(f"Thumbnail text is punchy ({len(thumb_words)} words).")

        # -------------------------------------------------------------
        # 3. First 30s Hook Quality
        # -------------------------------------------------------------
        clean_hook = hook.strip().lower()
        if not clean_hook or len(clean_hook.split()) < 5:
            score -= 18
            problems.append({
                "area": "Hook",
                "severity": "CRITICAL",
                "issue": "No strong retention hook defined for the start of the video.",
                "fix": "Add an open loop or shocking claim in the first 1-3s (Shorts) or 5-15s (Long-form).",
            })
        elif any(f in clean_hook for f in ["welcome to my channel", "in this video we are", "don't forget to subscribe before"]):
            score -= 12
            problems.append({
                "area": "Hook",
                "severity": "HIGH",
                "issue": "Hook contains low-retention filler phrases ('welcome back', 'in this video').",
                "fix": "Cut straight to the stakes or demonstration within the first 3 seconds.",
            })
        else:
            strengths.append("Retention hook jumps straight into stakes without filler.")

        # -------------------------------------------------------------
        # 4. Description Depth & Above-the-fold
        # -------------------------------------------------------------
        desc_words = len(description.strip().split())
        if desc_words < 50:
            score -= 10
            problems.append({
                "area": "Description",
                "severity": "MEDIUM",
                "issue": f"Description is sparse ({desc_words} words). Misses search indexing opportunity.",
                "fix": "Write a 150+ word overview with bullet points and external resources.",
            })
        else:
            strengths.append("Description contains rich context and search keywords.")

        # -------------------------------------------------------------
        # 5. Tags & Metadata
        # -------------------------------------------------------------
        if len(tags) < 8:
            score -= 8
            problems.append({
                "area": "Tags",
                "severity": "MEDIUM",
                "issue": f"Only {len(tags)} tags provided.",
                "fix": "Include 12–18 target long-tail keywords.",
            })

        # -------------------------------------------------------------
        # 6. Policy & Copyright Safety Gate
        # -------------------------------------------------------------
        lower_all = (title + " " + description + " " + script_text).lower()
        
        # Check for policy red flags
        toxic_terms = ["kill yourself", "how to hack bank", "free money glitch 100% real scam"]
        for term in toxic_terms:
            if term in lower_all:
                policy_risk = "CRITICAL"
                is_blocked = True
                score = 0
                problems.append({
                    "area": "Policy Safety",
                    "severity": "CRITICAL_BLOCK",
                    "issue": f"Detected potential YouTube Community Guidelines violation: '{term}'",
                    "fix": "Remove or rephrase violating terms immediately before publishing.",
                })

        # Check for obvious copyright risks
        if "universal music group" in lower_all or "disney official audio" in lower_all:
            copyright_risk = "HIGH"
            problems.append({
                "area": "Copyright Risk",
                "severity": "HIGH",
                "issue": "Script mentions commercial copyrighted music assets without licensing clearance.",
                "fix": "Use royalty-free audio from YouTube Audio Library or authorized providers.",
            })

        final_score = max(0, min(score, 100))
        verdict = "BLOCKED 🛑" if is_blocked else ("PASS ✅" if final_score >= 80 else "NEEDS FIX ⚠️")

        report = {
            "title": title,
            "final_publish_score": final_score,
            "verdict": verdict,
            "is_blocked": is_blocked,
            "policy_risk": policy_risk,
            "copyright_risk": copyright_risk,
            "strengths": strengths,
            "problems": problems,
            "can_approve": final_score >= 75 and not is_blocked,
        }

        # Save to database
        try:
            with get_db() as db:
                audit_rec = Audit(
                    audit_type="prepublish",
                    target_identifier=title[:100],
                    overall_score=final_score,
                    strengths_json=str(strengths),
                    problems_json=str(problems),
                    action_plan_json=str([p["fix"] for p in problems]),
                    full_report_json=str(report),
                )
                db.add(audit_rec)
        except Exception:
            pass

        return report

    @staticmethod
    def apply_auto_fixes(
        title: str,
        description: str,
        thumbnail_text: str,
    ) -> Dict[str, str]:
        """
        Automatically resolves common mechanical packaging issues (Section 22).
        """
        fixed_title = title.strip()
        if len(fixed_title) > 65:
            # Smart truncate at last word before 65 chars
            fixed_title = fixed_title[:62].rsplit(" ", 1)[0] + "..."

        # Fix thumbnail text to <= 3 punchy words
        words = thumbnail_text.strip().split()
        fixed_thumb_text = " ".join(words[:3]).upper() if words else "MUST WATCH!"

        # Fix description hook
        fixed_desc = description.strip()
        if len(fixed_desc.split()) < 30:
            fixed_desc = (
                f"In this video, we break down {title} step by step.\n\n"
                f"Make sure to watch until the end for the key revelation.\n"
                f"Subscribe for more weekly videos!\n\n"
                + fixed_desc
            )

        return {
            "fixed_title": fixed_title,
            "fixed_thumbnail_text": fixed_thumb_text,
            "fixed_description": fixed_desc,
        }
