"""Core business logic for cards and gate scans.

Kept separate from routes.py so both the /gate/scan HTTP endpoint and the
admin "manual correction" UI can share the exact same toggle/logging
logic instead of duplicating it.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from flask import current_app

from app.extensions import db
from app.models import Card, LogEntry, Member
from app.utils.tokens import generate_card_token


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def issue_card(member: Member) -> Card:
    """Revoke any existing active card and mint a fresh token."""
    for existing in member.cards:
        if existing.active:
            existing.revoke()
    token_bytes = current_app.config["CARD_TOKEN_BYTES"]
    card = Card(member=member, token=generate_card_token(token_bytes))
    db.session.add(card)
    return card


@dataclass
class ScanResult:
    status: str  # "checked_in" | "checked_out" | "rejected" | "debounced"
    member: Optional[Member] = None
    message: str = ""


def _log(event_type: str, *, member_id=None, staff_user_id=None, source="web-app", note=None, context=None):
    db.session.add(
        LogEntry(
            event_type=event_type,
            member_id=member_id,
            staff_user_id=staff_user_id,
            source=source,
            note=note,
            context_json=json.dumps(context) if context else None,
        )
    )


def process_gate_scan(token: str, *, source: str = "gate-scanner") -> ScanResult:
    """Look up a scanned token, toggle the member's check-in status, and
    write the corresponding audit log entry (which also feeds the
    statistics dashboard). Debounces rapid repeat scans of the same card
    so an accidental double-tap doesn't flip the status twice.
    """
    token = (token or "").strip()
    if not token:
        _log("scan_rejected", source=source, note="empty token")
        db.session.commit()
        return ScanResult(status="rejected", message="Ingen kod avläst.")

    card = Card.query.filter_by(token=token, active=True).first()
    if card is None:
        _log("scan_rejected", source=source, note="unknown or inactive token")
        db.session.commit()
        return ScanResult(status="rejected", message="Okänt eller inaktiverat kort.")

    member = card.member
    if not member.active:
        _log("scan_rejected", member_id=member.id, source=source, note="inactive member")
        db.session.commit()
        return ScanResult(status="rejected", message="Kortet är inaktiverat.")

    debounce_seconds = current_app.config["SCAN_DEBOUNCE_SECONDS"]
    if member.status_updated_at is not None:
        elapsed = utcnow() - _as_aware(member.status_updated_at)
        if elapsed < timedelta(seconds=debounce_seconds):
            return ScanResult(
                status="debounced", member=member, message="Redan registrerad, väntar en stund."
            )

    if member.current_status == "in":
        member.current_status = "out"
        event_type = "check_out"
        result_status = "checked_out"
    else:
        member.current_status = "in"
        event_type = "check_in"
        result_status = "checked_in"

    member.status_updated_at = utcnow()
    _log(event_type, member_id=member.id, source=source)
    db.session.commit()
    return ScanResult(status=result_status, member=member)


def manual_set_status(member: Member, new_status: str, staff_user_id: int) -> None:
    """Staff correction of a member's checked in/out status from the admin UI."""
    if new_status not in {"in", "out"}:
        raise ValueError("new_status must be 'in' or 'out'")
    member.current_status = new_status
    member.status_updated_at = utcnow()
    event_type = "manual_check_in" if new_status == "in" else "manual_check_out"
    _log(event_type, member_id=member.id, staff_user_id=staff_user_id, source="admin")
    db.session.commit()


def _as_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def auto_checkout_all(staff_user_id: Optional[int] = None) -> int:
    """Reset every currently-checked-in member to "out". Intended to run
    once nightly (see scripts/retention_cleanup.py or a cron/systemd
    timer) so a missed gate scan can't leave someone marked "in" forever.
    """
    members = Member.query.filter_by(current_status="in", active=True).all()
    for member in members:
        member.current_status = "out"
        member.status_updated_at = utcnow()
        _log(
            "manual_check_out",
            member_id=member.id,
            staff_user_id=staff_user_id,
            source="system",
            note="auto checkout",
        )
    db.session.commit()
    return len(members)
