import csv
import io

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.admin import stats
from app.admin.forms import EditMemberForm, ManualAttendanceForm, MemberSearchForm, RegisterMemberForm
from app.admin.services import erase_member_personal_data, register_member
from app.card.services import issue_card, manual_set_status
from app.extensions import db
from app.models import LogEntry, Member

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
def require_login():
    pass


@admin_bp.route("/")
def dashboard():
    visits_by_day = stats.visits_by_day(days=14)
    popular_hours = stats.popular_hours(days=30)
    return render_template(
        "admin/stats_dashboard.html",
        active_now=stats.active_now(),
        visits_by_day=visits_by_day,
        max_visits_by_day=max((count for _, count in visits_by_day), default=0),
        popular_hours=popular_hours,
        max_popular_hours=max((count for _, count in popular_hours), default=0),
        unique_visitors=stats.unique_visitors(days=30),
    )


@admin_bp.route("/register", methods=["GET", "POST"])
def register_member_view():
    form = RegisterMemberForm()
    new_pin = None
    new_qr_url = None
    registered_member = None
    if form.validate_on_submit():
        result = register_member(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            source="admin",
            staff_user_id=current_user.id,
        )
        flash(
            f"{result.member.full_name()} registrerad. PIN-kod: {result.raw_pin} (visa endast en gång).",
            "success",
        )
        new_pin = result.raw_pin
        new_qr_url = url_for("card.card_qr_image", card_id=result.card_id)
        registered_member = result.member
        return render_template(
            "admin/register_member.html",
            form=RegisterMemberForm(),
            new_pin=new_pin,
            new_qr_url=new_qr_url,
            registered_member=registered_member,
        )

    return render_template("admin/register_member.html", form=form, new_pin=None, new_qr_url=None)


@admin_bp.route("/members/search")
def members_search():
    form = MemberSearchForm(request.args, meta={"csrf": False})
    results = []
    if form.query.data:
        needle = f"%{form.query.data.strip()}%"
        results = (
            Member.query.filter(Member.active.is_(True))
            .filter((Member.first_name.ilike(needle)) | (Member.last_name.ilike(needle)))
            .order_by(Member.last_name, Member.first_name)
            .limit(50)
            .all()
        )
    return render_template("admin/member_search.html", form=form, results=results)


@admin_bp.route("/members/<int:member_id>")
def member_detail(member_id: int):
    member = db.session.get(Member, member_id) or abort(404)
    form = ManualAttendanceForm()
    return render_template("admin/member_detail.html", member=member, form=form)


@admin_bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
def edit_member(member_id: int):
    member = db.session.get(Member, member_id) or abort(404)

    form = EditMemberForm(obj=member)

    if form.validate_on_submit():
        member.first_name = form.first_name.data.strip()
        member.last_name = form.last_name.data.strip()
        member.phone = (form.phone.data or "").strip() or None

        db.session.add(
            LogEntry(
                event_type="member_updated",
                member_id=member.id,
                staff_user_id=current_user.id,
                source="admin",
            )
        )
        db.session.commit()
        flash(f"{member.full_name()} uppdaterad.", "success")
        return redirect(url_for("admin.member_detail", member_id=member.id))

    return render_template("admin/edit_member.html", form=form, member=member)


@admin_bp.route("/members/<int:member_id>/reissue-card", methods=["POST"])
def reissue_card(member_id: int):
    member = db.session.get(Member, member_id) or abort(404)
    issue_card(member)
    db.session.add(
        LogEntry(
            event_type="card_reissued", member_id=member.id, staff_user_id=current_user.id, source="admin"
        )
    )
    db.session.commit()
    flash(f"Nytt kort utfärdat för {member.full_name()}.", "success")
    return redirect(url_for("admin.member_detail", member_id=member.id))


@admin_bp.route("/members/<int:member_id>/revoke-card", methods=["POST"])
def revoke_card(member_id: int):
    member = db.session.get(Member, member_id) or abort(404)
    card = member.active_card()
    if card:
        card.revoke()
        db.session.add(
            LogEntry(
                event_type="card_revoked", member_id=member.id, staff_user_id=current_user.id, source="admin"
            )
        )
        db.session.commit()
        flash(f"Kortet för {member.full_name()} är nu inaktiverat.", "warning")
    return redirect(url_for("admin.member_detail", member_id=member.id))


@admin_bp.route("/members/<int:member_id>/manual-status/<status>", methods=["POST"])
def manual_status(member_id: int, status: str):
    member = db.session.get(Member, member_id) or abort(404)
    if status not in {"in", "out"}:
        abort(400)
    manual_set_status(member, status, current_user.id)
    new_status_label = "incheckad" if status == "in" else "utcheckad"
    flash(f"{member.full_name()} manuellt satt till {new_status_label}.", "info")
    return redirect(request.referrer or url_for("admin.attendance_live"))


@admin_bp.route("/members/<int:member_id>/delete", methods=["POST"])
def delete_member(member_id: int):
    member = db.session.get(Member, member_id) or abort(404)
    erase_member_personal_data(member, staff_user_id=current_user.id, source="admin")
    db.session.commit()
    flash("Personens uppgifter har raderats.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/attendance")
def attendance_live():
    checked_in = (
        Member.query.filter_by(current_status="in", active=True)
        .order_by(Member.status_updated_at.desc())
        .all()
    )
    return render_template("admin/attendance_live.html", checked_in=checked_in)


@admin_bp.route("/logs")
def audit_log():
    page = request.args.get("page", 1, type=int)
    pagination = LogEntry.query.order_by(LogEntry.timestamp.desc()).paginate(page=page, per_page=50)
    return render_template("admin/audit_log.html", pagination=pagination)


@admin_bp.route("/logs/export.csv")
def audit_log_export():
    entries = LogEntry.query.order_by(LogEntry.timestamp.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["timestamp", "event_type", "member_id", "member_name", "staff_user_id", "source", "note"]
    )
    for entry in entries:
        member_name = entry.member.full_name() if entry.member else ""
        writer.writerow(
            [entry.timestamp.isoformat(), entry.event_type, entry.member_id or "", member_name,
             entry.staff_user_id or "", entry.source, entry.note or ""]
        )
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=gardskort-logg.csv"},
    )
