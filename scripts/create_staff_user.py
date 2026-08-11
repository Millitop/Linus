"""Create (or reset the password of) a staff admin account.

    python scripts/create_staff_user.py <username> [--display-name "Namn"] [--role admin]

Prompts for a password interactively (never pass it as a CLI argument --
it would end up in shell history).
"""
import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import StaffUser  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("--display-name", default=None)
    parser.add_argument("--role", default="staff", choices=["staff", "admin"])
    args = parser.parse_args()

    password = getpass.getpass("Lösenord: ")
    confirm = getpass.getpass("Upprepa lösenord: ")
    if password != confirm:
        print("Lösenorden matchar inte.", file=sys.stderr)
        sys.exit(1)
    if len(password) < 8:
        print("Lösenordet måste vara minst 8 tecken.", file=sys.stderr)
        sys.exit(1)

    app = create_app()
    with app.app_context():
        user = StaffUser.query.filter_by(username=args.username).first()
        if user is None:
            user = StaffUser(username=args.username, role=args.role, display_name=args.display_name)
            db.session.add(user)
            action = "skapad"
        else:
            user.role = args.role
            user.display_name = args.display_name or user.display_name
            action = "uppdaterad"
        user.set_password(password)
        user.active = True
        db.session.commit()
        print(f"Personalanvändare {args.username!r} {action}.")


if __name__ == "__main__":
    main()
