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
from app.models import Card, Child, LogEntry
from app.utils.tokens import generate_card_token


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def issue_card(child: Child) -> Card:
    """Revoke any existing active card and mint a fresh token."""
    for existing in child.cards:
        if existing.active:
            existing.revoke()
    token_bytes = current_app.config["CARD_TOKEN_BYTES"]
    card = Card(child=child, token=generate_card_token(token_bytes))
    db.session.add(card)
    return card


@dataclass
class ScanResult:
    status: str  # "checked_in" | "checked_out" | "rejected" | "debounced"
    child: Optional[Child] = None
    message: str = ""


def _log(event_type: str, *, child_id=None, staff_user_id=None, source="web-app", note=None, context=None):
    db.session.add(
        LogEntry(
            event_type=event_type,
            child_id=child_id,
            staff_user_id=staff_user_id,
            source=source,
            note=note,
            context_json=json.dumps(context) if context else None,
        )
    )


def process_gate_scan(token: str, *, source: str = "gate-scanner") -> ScanResult:
    """Look up a scanned token, toggle the child's check-in status, and
    write the corresponding audit log entry. Debounces rapid repeat scans
    of the same card so an accidental double-tap doesn't flip the status
    twice.
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

    child = card.child
    if not child.active:
        _log("scan_rejected", child_id=child.id, source=source, note="inactive child")
        db.session.commit()
        return ScanResult(status="rejected", message="Kortet är inaktiverat.")

    debounce_seconds = current_app.config["SCAN_DEBOUNCE_SECONDS"]
    if child.status_updated_at is not None:
        elapsed = utcnow() - _as_aware(child.status_updated_at)
        if elapsed < timedelta(seconds=debounce_seconds):
            return ScanResult(status="debounced", child=child, message="Redan registrerad, väntar en stund.")

    if child.current_status == "in":
        child.current_status = "out"
        event_type = "check_out"
        result_status = "checked_out"
    else:
        child.current_status = "in"
        event_type = "check_in"
        result_status = "checked_in"

    child.status_updated_at = utcnow()
    _log(event_type, child_id=child.id, source=source)
    db.session.commit()
    return ScanResult(status=result_status, child=child)


def manual_set_status(child: Child, new_status: str, staff_user_id: int) -> None:
    """Staff correction of a child's checked in/out status from the admin UI."""
    if new_status not in {"in", "out"}:
        raise ValueError("new_status must be 'in' or 'out'")
    child.current_status = new_status
    child.status_updated_at = utcnow()
    event_type = "manual_check_in" if new_status == "in" else "manual_check_out"
    _log(event_type, child_id=child.id, staff_user_id=staff_user_id, source="admin")
    db.session.commit()


def _as_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def auto_checkout_all(staff_user_id: Optional[int] = None) -> int:
    """Reset every currently-checked-in child to "out". Intended to run
    once nightly (see scripts/retention_cleanup.py or a cron/systemd
    timer) so a missed gate scan can't leave a child marked "in" forever.
    """
    children = Child.query.filter_by(current_status="in", active=True).all()
    for child in children:
        child.current_status = "out"
        child.status_updated_at = utcnow()
        _log(
            "manual_check_out",
            child_id=child.id,
            staff_user_id=staff_user_id,
            source="system",
            note="auto checkout",
        )
    db.session.commit()
    return len(children)
