"""Create all database tables. Run once before first use:

    python scripts/init_db.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402


def main() -> None:
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Databastabeller skapade.")


if __name__ == "__main__":
    main()
