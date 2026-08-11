from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.forms import StaffLoginForm
from app.extensions import db, limiter
from app.models import LogEntry, StaffUser

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = StaffLoginForm()
    if form.validate_on_submit():
        user = StaffUser.query.filter_by(username=form.username.data.strip()).first()
        if user and user.active and user.check_password(form.password.data):
            login_user(user)
            user.last_login_at = datetime.now(timezone.utc)
            db.session.add(
                LogEntry(event_type="staff_login", staff_user_id=user.id, source="web-app")
            )
            db.session.commit()
            next_url = request.args.get("next")
            return redirect(next_url or url_for("admin.dashboard"))
        flash("Fel användarnamn eller lösenord.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    db.session.add(
        LogEntry(event_type="staff_logout", staff_user_id=current_user.id, source="web-app")
    )
    db.session.commit()
    logout_user()
    flash("Du är utloggad.", "info")
    return redirect(url_for("auth.login"))
