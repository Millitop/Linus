"""Database models.

Data minimization is deliberate: no national ID numbers, home addresses,
or photos are stored anywhere in this schema -- only what is needed to
issue a card and keep a safety/statistics-relevant check-in log. See
docs/gdpr-and-retention.md for the reasoning.
"""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Member(db.Model):
    """A young person who self-registers for a gårdskort at the
    fritidsgård. No guardian/parent link is required -- members are
    older youths who sign themselves up.
    """

    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(40), nullable=True)

    current_status = db.Column(db.String(10), nullable=False, default="out")  # "in" | "out"
    status_updated_at = db.Column(db.DateTime, nullable=True)

    retrieval_pin_hash = db.Column(db.String(255), nullable=True)

    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    emergency_contacts = db.relationship(
        "EmergencyContact", backref="member", cascade="all, delete-orphan", lazy="selectin"
    )
    cards = db.relationship("Card", backref="member", cascade="all, delete-orphan", lazy="selectin")
    log_entries = db.relationship("LogEntry", backref="member", lazy="dynamic")

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def active_card(self):
        return next((c for c in self.cards if c.active), None)

    def set_retrieval_pin(self, raw_pin: str) -> None:
        self.retrieval_pin_hash = generate_password_hash(raw_pin)

    def check_retrieval_pin(self, raw_pin: str) -> bool:
        if not self.retrieval_pin_hash:
            return False
        return check_password_hash(self.retrieval_pin_hash, raw_pin)

    def last_activity_at(self):
        """Timestamp of the member's most recent check-in/out, used by
        the inactivity-based retention job. Falls back to
        ``created_at`` for a member who registered but never checked in.
        """
        latest = (
            self.log_entries.filter(LogEntry.event_type.in_(["check_in", "check_out"]))
            .order_by(LogEntry.timestamp.desc())
            .first()
        )
        return latest.timestamp if latest else self.created_at

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Member {self.id} {self.full_name()!r}>"


class EmergencyContact(db.Model):
    """Optional contact for a member -- not required to register, since
    members are older youths signing themselves up (not a guardian-run
    enrollment). Staff or the member can add one later if wanted.
    """

    __tablename__ = "emergency_contacts"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    relationship_label = db.Column(db.String(40), nullable=True)  # e.g. "förälder", "syskon"


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    def revoke(self) -> None:
        self.active = False
        self.revoked_at = utcnow()


class StaffUser(UserMixin, db.Model):
    __tablename__ = "staff_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="staff")  # "staff" | "admin"
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self) -> bool:  # overrides UserMixin default
        return self.active


class LogEntry(db.Model):
    """Unified audit log for every registration, card retrieval and
    check-in/out event. See docs/event-taxonomy.md for the full list of
    event_type values and when each is written. Also the source data for
    the statistics dashboard (app/admin/stats.py).
    """

    __tablename__ = "log_entries"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(40), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=True, index=True)
    staff_user_id = db.Column(db.Integer, db.ForeignKey("staff_users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    source = db.Column(db.String(20), nullable=False, default="web-app")  # gate-scanner|web-app|admin|system
    context_json = db.Column(db.Text, nullable=True)
    note = db.Column(db.String(255), nullable=True)

    staff_user = db.relationship("StaffUser")
