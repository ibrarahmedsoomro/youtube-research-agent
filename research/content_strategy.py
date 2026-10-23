"""
Content Strategy Planner (Section 10).
Generates structured 7, 14, 30, 60, or 90-day publishing schedules with Days, Topics, Titles, Hooks, and Formats.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from database.db import get_db, log_system_event
from database.models import ContentCalendarItem


class ContentStrategyEngine:
    @staticmethod
    def generate_strategy_plan(
        niche: str,
        days_duration: int = 7,  # 7, 14, 30, 60, 90
        start_date: str = "",
    ) -> Dict[str, Any]:
        """
        Creates a day-by-day roadmap with balanced long-form and Shorts cadence.
        """
        log_system_event("ContentStrategy", f"Generating {days_duration}-day strategy for {niche}")
        
        base_date = datetime.now(timezone.utc)
        if start_date:
            try:
                base_date = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                pass

        plan = []
        # Alternating rhythm: Long-form on Day 1 & 4; Shorts on Day 2, 3, 5, 6; Review on Day 7
        for i in range(1, days_duration + 1):
            target_date = (base_date + timedelta(days=i - 1)).strftime("%Y-%m-%d")
            
            if i % 3 == 1:
                fmt = "Long-form (8-12m)"
                topic_type = "Core Pillar Tutorial / Deep Dive"
                title = f"The Definitive {niche.title()} Blueprint in 2026"
                hook = "Everything you've been taught about this topic is missing one crucial ingredient."
            elif i % 3 == 2:
                fmt = "Shorts (30-45s)"
                topic_type = "Micro Tip / Myth Buster"
                title = f"Don't Do This in {niche.title()}!"
                hook = "Stop making this rookie mistake before you waste another hour."
            else:
                fmt = "Shorts (45-60s)"
                topic_type = "Behind The Scenes / POV Case Study"
                title = f"How I Solved The Hardest Problem in {niche.title()}"
                hook = "I almost gave up when this happened..."

            day_item = {
                "day_number": i,
                "date": target_date,
                "format": fmt,
                "topic_type": topic_type,
                "title": title,
                "hook": hook,
                "status": "PLANNED",
            }
            plan.append(day_item)

            # Save to ContentCalendar table
            try:
                with get_db() as db:
                    cal_entry = ContentCalendarItem(
                        title=title,
                        format=fmt,
                        scheduled_date=target_date,
                        status="PLANNED",
                        notes=f"{topic_type} - Hook: {hook}",
                    )
                    db.add(cal_entry)
            except Exception:
                pass

        return {
            "niche": niche,
            "duration_days": days_duration,
            "schedule": plan,
        }
