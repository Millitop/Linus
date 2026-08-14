"""Shared logic for admin-side child management.

Kept separate from routes.py so the manual "radera personuppgifter"
button and the automatic nightly age-based purge
(scripts/retention_cleanup.py) use exactly the same erasure behaviour
instead of two diverging implementations.
"""
from datetime import datetime, timezone
from typing import Optional

from app.extensions import db
from app.models import Child, LogEntry


def erase_child_personal_data(
    child: Child, *, staff_user_id: Optional[int] = None, source: str = "admin", note: Optional[str] = None
) -> None:
    """GDPR erasure: revoke all cards, drop guardian contacts, and scrub
    personal fields on the Child row -- while keeping the row itself and
    the audit log's historical entries (with child_id retained for
    safety-log continuity) intact. See docs/gdpr-and-retention.md.
    """
    for card in child.cards:
        card.revoke()
    for guardian in list(child.guardians):
        db.session.delete(guardian)

    child.first_name = "Raderad"
    child.last_name = "Raderad"
    child.group_class = None
    child.birth_year = None
    child.retrieval_pin_hash = None
    child.active = False
    child.deleted_at = datetime.now(timezone.utc)

    db.session.add(
        LogEntry(
            event_type="child_data_deleted",
            child_id=child.id,
            staff_user_id=staff_user_id,
            source=source,
            note=note,
        )
    )


def purge_children_who_turned_adult(threshold_years: int) -> int:
    """Erase personal data for every active child who has reached
    ``threshold_years`` of age. Intended to run nightly alongside the
    other retention jobs in scripts/retention_cleanup.py. Returns the
    number of children erased.
    """
    if threshold_years <= 0:
        return 0

    candidates = Child.query.filter(Child.active.is_(True), Child.birth_year.isnot(None)).all()
    erased = 0
    for child in candidates:
        if child.is_adult(threshold_years):
            erase_child_personal_data(
                child, source="system", note=f"auto: reached {threshold_years} års ålder"
            )
            erased += 1

    if erased:
        db.session.commit()
    return erased
