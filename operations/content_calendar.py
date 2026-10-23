"""
Content Calendar Module (Section 25).
Visual calendar management tracking Planned, Draft, Ready, Scheduled, and Published videos.
"""

from typing import List, Dict, Any
from database.db import get_db, log_system_event
from database.models import ContentCalendarItem


class ContentCalendarManager:
    @staticmethod
    def get_calendar_items() -> List[Dict[str, Any]]:
        """Fetches all items ordered by scheduled date."""
        with get_db() as db:
            items = db.query(ContentCalendarItem).order_by(ContentCalendarItem.scheduled_date.asc()).all()
            return [
                {
                    "id": i.id,
                    "title": i.title,
                    "format": i.format,
                    "scheduled_date": i.scheduled_date,
                    "status": i.status,
                    "notes": i.notes or "",
                }
                for i in items
            ]

    @staticmethod
    def add_calendar_item(title: str, scheduled_date: str, format_type: str = "Shorts", status: str = "PLANNED", notes: str = "") -> int:
        """Adds a scheduled slot to the calendar."""
        log_system_event("ContentCalendar", f"Scheduling {title[:30]} for {scheduled_date}")
        with get_db() as db:
            entry = ContentCalendarItem(
                title=title,
                scheduled_date=scheduled_date,
                format=format_type,
                status=status,
                notes=notes,
            )
            db.add(entry)
            db.flush()
            return entry.id

    @staticmethod
    def update_item_status(item_id: int, new_status: str) -> bool:
        with get_db() as db:
            item = db.query(ContentCalendarItem).filter(ContentCalendarItem.id == item_id).first()
            if item:
                item.status = new_status
                return True
        return False
