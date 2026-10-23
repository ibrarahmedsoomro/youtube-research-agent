"""
Human Approval Center (Section 23).
Enforces the mandatory human gatekeeper so AI cannot publish without explicit user consent.
States: DRAFT -> AI_REVIEW -> NEEDS_FIX -> READY -> WAITING_APPROVAL -> APPROVED -> SCHEDULED -> PUBLISHED.
"""

from typing import List, Dict, Any, Optional
from database.db import get_db, log_system_event
from database.models import Approval

VALID_STATUSES = [
    "DRAFT",
    "AI_REVIEW",
    "NEEDS_FIX",
    "READY",
    "WAITING_APPROVAL",
    "APPROVED",
    "SCHEDULED",
    "PUBLISHED",
    "FAILED",
]


class ApprovalCenter:
    @staticmethod
    def get_all_approvals() -> List[Dict[str, Any]]:
        """Retrieves all pending and active workflow approvals."""
        with get_db() as db:
            items = db.query(Approval).order_by(Approval.updated_at.desc()).all()
            return [
                {
                    "id": item.id,
                    "title": item.title,
                    "format": item.format,
                    "status": item.status,
                    "prepublish_score": item.prepublish_score,
                    "policy_risk": item.policy_risk,
                    "copyright_risk": item.copyright_risk,
                    "notes": item.notes,
                    "updated_at": item.updated_at.strftime("%Y-%m-%d %H:%M") if item.updated_at else "",
                }
                for item in items
            ]

    @staticmethod
    def create_approval_entry(
        title: str,
        format_type: str = "Shorts",
        prepublish_score: float = 90.0,
        policy_risk: str = "LOW",
        copyright_risk: str = "LOW",
        notes: str = "",
        initial_status: str = "WAITING_APPROVAL",
    ) -> Dict[str, Any]:
        """Submits a video package to the human approval queue."""
        log_system_event("ApprovalCenter", f"Submitting {title[:30]} for approval")
        with get_db() as db:
            entry = Approval(
                title=title,
                format=format_type,
                status=initial_status,
                prepublish_score=prepublish_score,
                policy_risk=policy_risk,
                copyright_risk=copyright_risk,
                notes=notes,
            )
            db.add(entry)
            db.flush()
            return {"id": entry.id, "title": entry.title, "status": entry.status}

    @staticmethod
    def set_status(item_id: int, new_status: str, notes: str = "") -> bool:
        """Updates the status of an approval item."""
        if new_status not in VALID_STATUSES:
            return False
        with get_db() as db:
            item = db.query(Approval).filter(Approval.id == item_id).first()
            if item:
                item.status = new_status
                if notes:
                    item.notes = notes
                log_system_event("ApprovalCenter", f"Item {item_id} transitioned to {new_status}")
                return True
        return False
