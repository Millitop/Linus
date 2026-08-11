"""Nightly maintenance job: auto-checkout everyone still marked "in", and
purge log entries older than LOG_RETENTION_DAYS (0 disables purging).

Intended to run once per night via a systemd timer or cron, e.g.:

    0 3 * * * /home/pi/linus/.venv/bin/python /home/pi/linus/scripts/retention_cleanup.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.card.services import auto_checkout_all  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import LogEntry  # noqa: E402


def purge_old_logs(retention_days: int) -> int:
    if retention_days <= 0:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = LogEntry.query.filter(LogEntry.timestamp < cutoff).delete(synchronize_session=False)
    db.session.commit()
    return deleted


def main() -> None:
    app = create_app()
    with app.app_context():
        checked_out = auto_checkout_all()
        print(f"Automatisk utcheckning: {checked_out} barn.")

        retention_days = app.config["LOG_RETENTION_DAYS"]
        deleted = purge_old_logs(retention_days)
        print(f"Gallrade {deleted} loggposter äldre än {retention_days} dagar.")


if __name__ == "__main__":
    main()
