"""Shared logic for member registration and management.

Kept separate from routes.py so the public self-registration route
(/join), the staff-assisted admin registration route, the manual
"radera personuppgifter" button, and the automatic nightly inactivity
purge (scripts/retention_cleanup.py) all share the exact same
behaviour instead of diverging implementations.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.card.services import issue_card
from app.extensions import db
from app.models import LogEntry, Member
from app.utils.tokens import generate_retrieval_pin


@dataclass
class RegistrationResult:
    member: Member
    raw_pin: str
    card_id: int


def register_member(
    *,
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    source: str,
    staff_user_id: Optional[int] = None,
) -> RegistrationResult:
    """Create a new member, mint their first card, and log the
    registration event. Used both by the public self-registration route
    (source="web-app") and by staff helping someone register in person
    (source="admin").
    """
    member = Member(
        first_name=first_name.strip(), last_name=last_name.strip(), phone=(phone or "").strip() or None
    )
    raw_pin = generate_retrieval_pin()
    member.set_retrieval_pin(raw_pin)
    db.session.add(member)

    card = issue_card(member)
    db.session.flush()  # assign member.id before we reference it below

    db.session.add(
        LogEntry(event_type="registration", member_id=member.id, staff_user_id=staff_user_id, source=source)
    )
    db.session.commit()

    return RegistrationResult(member=member, raw_pin=raw_pin, card_id=card.id)


def erase_member_personal_data(
    member: Member, *, staff_user_id: Optional[int] = None, source: str = "admin", note: Optional[str] = None
) -> None:
    """GDPR erasure: revoke all cards, drop emergency contacts, and
    scrub personal fields on the Member row -- while keeping the row
    itself and the audit log's historical entries (with member_id
    retained for continuity) intact. See docs/gdpr-and-retention.md.
    """
    for card in member.cards:
        card.revoke()
    for contact in list(member.emergency_contacts):
        db.session.delete(contact)

    member.first_name = "Raderad"
    member.last_name = "Raderad"
    member.phone = None
    member.retrieval_pin_hash = None
    member.active = False
    member.deleted_at = datetime.now(timezone.utc)

    db.session.add(
        LogEntry(
            event_type="member_data_deleted",
            member_id=member.id,
            staff_user_id=staff_user_id,
            source=source,
            note=note,
        )
    )


def purge_inactive_members(inactive_months: int) -> int:
    """Erase personal data for every active member whose last check-in
    activity (or registration, if they never checked in) is older than
    ``inactive_months``. Intended to run nightly alongside the other
    retention jobs in scripts/retention_cleanup.py. Returns the number
    of members erased. 0 disables this entirely.
    """
    if inactive_months <= 0:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=inactive_months * 30)
    erased = 0
    for member in Member.query.filter_by(active=True).all():
        last_active = member.last_activity_at()
        if last_active and _as_aware(last_active) < cutoff:
            erase_member_personal_data(
                member, source="system", note=f"auto: inaktiv i {inactive_months}+ månader"
            )
            erased += 1

    if erased:
        db.session.commit()
    return erased


def _as_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
