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

from app.admin.forms import EditChildForm, ManualAttendanceForm, RegisterChildForm
from app.admin.services import erase_child_personal_data
from app.card.services import issue_card, manual_set_status
from app.extensions import db
from app.models import Child, GuardianContact, LogEntry
from app.utils.tokens import generate_retrieval_pin

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
def require_login():
    pass


@admin_bp.route("/")
def dashboard():
    checked_in_count = Child.query.filter_by(current_status="in", active=True).count()
    total_active = Child.query.filter_by(active=True).count()
    recent = LogEntry.query.order_by(LogEntry.timestamp.desc()).limit(10).all()
    return render_template(
        "admin/dashboard.html",
        checked_in_count=checked_in_count,
        total_active=total_active,
        recent=recent,
    )


@admin_bp.route("/register", methods=["GET", "POST"])
def register_child():
    form = RegisterChildForm()
    new_pin = None
    new_qr_url = None
    if form.validate_on_submit():
        child = Child(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            group_class=(form.group_class.data or "").strip() or None,
            birth_year=form.birth_year.data or None,
        )
        raw_pin = generate_retrieval_pin()
        child.set_retrieval_pin(raw_pin)
        db.session.add(child)

        guardian = GuardianContact(
            child=child,
            name=form.guardian_name.data.strip(),
            phone=(form.guardian_phone.data or "").strip() or None,
            email=(form.guardian_email.data or "").strip() or None,
            relationship_label="vårdnadshavare",
            primary_contact=True,
        )
        db.session.add(guardian)

        card = issue_card(child)
        db.session.flush()  # assign child.id before we reference it below

        db.session.add(
            LogEntry(
                event_type="registration",
                child_id=child.id,
                staff_user_id=current_user.id,
                source="admin",
            )
        )
        db.session.commit()

        flash(f"{child.full_name()} registrerad. PIN-kod: {raw_pin} (visa endast en gång).", "success")
        new_pin = raw_pin
        new_qr_url = url_for("card.card_qr_image", card_id=card.id)
        return render_template(
            "admin/register_child.html",
            form=RegisterChildForm(),
            new_pin=new_pin,
            new_qr_url=new_qr_url,
            registered_child=child,
        )

    return render_template("admin/register_child.html", form=form, new_pin=None, new_qr_url=None)


@admin_bp.route("/children")
def children_list():
    children = Child.query.filter_by(active=True).order_by(Child.last_name, Child.first_name).all()
    return render_template("admin/children_list.html", children=children)


@admin_bp.route("/children/<int:child_id>")
def child_detail(child_id: int):
    child = db.session.get(Child, child_id) or abort(404)
    form = ManualAttendanceForm()
    return render_template("admin/child_detail.html", child=child, form=form)


@admin_bp.route("/children/<int:child_id>/edit", methods=["GET", "POST"])
def edit_child(child_id: int):
    child = db.session.get(Child, child_id) or abort(404)
    guardian = next((g for g in child.guardians if g.primary_contact), None) or (
        child.guardians[0] if child.guardians else None
    )

    form = EditChildForm(obj=child)
    if guardian and request.method == "GET":
        form.guardian_name.data = guardian.name
        form.guardian_phone.data = guardian.phone
        form.guardian_email.data = guardian.email

    if form.validate_on_submit():
        child.first_name = form.first_name.data.strip()
        child.last_name = form.last_name.data.strip()
        child.group_class = (form.group_class.data or "").strip() or None
        child.birth_year = form.birth_year.data or None

        if guardian is None:
            guardian = GuardianContact(child=child, relationship_label="vårdnadshavare", primary_contact=True)
            db.session.add(guardian)
        guardian.name = form.guardian_name.data.strip()
        guardian.phone = (form.guardian_phone.data or "").strip() or None
        guardian.email = (form.guardian_email.data or "").strip() or None

        db.session.add(
            LogEntry(
                event_type="child_updated", child_id=child.id, staff_user_id=current_user.id, source="admin"
            )
        )
        db.session.commit()
        flash(f"{child.full_name()} uppdaterad.", "success")
        return redirect(url_for("admin.child_detail", child_id=child.id))

    return render_template("admin/edit_child.html", form=form, child=child)


@admin_bp.route("/children/<int:child_id>/reissue-card", methods=["POST"])
def reissue_card(child_id: int):
    child = db.session.get(Child, child_id) or abort(404)
    issue_card(child)
    db.session.add(
        LogEntry(
            event_type="card_reissued", child_id=child.id, staff_user_id=current_user.id, source="admin"
        )
    )
    db.session.commit()
    flash(f"Nytt kort utfärdat för {child.full_name()}.", "success")
    return redirect(url_for("admin.child_detail", child_id=child.id))


@admin_bp.route("/children/<int:child_id>/revoke-card", methods=["POST"])
def revoke_card(child_id: int):
    child = db.session.get(Child, child_id) or abort(404)
    card = child.active_card()
    if card:
        card.revoke()
        db.session.add(
            LogEntry(
                event_type="card_revoked", child_id=child.id, staff_user_id=current_user.id, source="admin"
            )
        )
        db.session.commit()
        flash(f"Kortet för {child.full_name()} är nu inaktiverat.", "warning")
    return redirect(url_for("admin.child_detail", child_id=child.id))


@admin_bp.route("/children/<int:child_id>/manual-status/<status>", methods=["POST"])
def manual_status(child_id: int, status: str):
    child = db.session.get(Child, child_id) or abort(404)
    if status not in {"in", "out"}:
        abort(400)
    manual_set_status(child, status, current_user.id)
    flash(f"{child.full_name()} manuellt satt till {'incheckad' if status == 'in' else 'utcheckad'}.", "info")
    return redirect(request.referrer or url_for("admin.attendance_live"))


@admin_bp.route("/children/<int:child_id>/delete", methods=["POST"])
def delete_child(child_id: int):
    child = db.session.get(Child, child_id) or abort(404)
    erase_child_personal_data(child, staff_user_id=current_user.id, source="admin")
    db.session.commit()
    flash("Barnets personuppgifter har raderats.", "warning")
    return redirect(url_for("admin.children_list"))


@admin_bp.route("/attendance")
def attendance_live():
    checked_in = (
        Child.query.filter_by(current_status="in", active=True)
        .order_by(Child.status_updated_at.desc())
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
    writer.writerow(["timestamp", "event_type", "child_id", "child_name", "staff_user_id", "source", "note"])
    for entry in entries:
        child_name = entry.child.full_name() if entry.child else ""
        writer.writerow(
            [entry.timestamp.isoformat(), entry.event_type, entry.child_id or "", child_name,
             entry.staff_user_id or "", entry.source, entry.note or ""]
        )
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=gardskort-logg.csv"},
    )
