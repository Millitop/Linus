from flask import Blueprint, Response, abort, flash, jsonify, render_template, request, url_for

from app.admin.services import register_member
from app.card.services import process_gate_scan
from app.extensions import csrf, db, limiter
from app.models import Card, LogEntry, Member
from app.utils.qr import token_to_qr_png_bytes

card_bp = Blueprint("card", __name__)


@card_bp.route("/join", methods=["GET", "POST"])
@csrf.exempt  # public self-registration page, no staff session
@limiter.limit("20 per minute")
def join():
    """Public self-registration: a member signs themselves up (no
    guardian/staff involvement needed) and gets their QR gårdskort
    immediately. This is the primary way people join the fritidsgård.
    """
    new_pin = None
    new_qr_url = None
    new_member_name = None
    if request.method == "POST":
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        phone = (request.form.get("phone") or "").strip()

        if not first_name or not last_name:
            flash("Förnamn och efternamn krävs.", "danger")
        else:
            result = register_member(
                first_name=first_name, last_name=last_name, phone=phone, source="web-app"
            )
            new_pin = result.raw_pin
            new_qr_url = url_for("card.card_qr_image", card_id=result.card_id)
            new_member_name = result.member.full_name()

    return render_template(
        "card/join.html", new_pin=new_pin, new_qr_url=new_qr_url, new_member_name=new_member_name
    )


@card_bp.route("/card/<int:card_id>/qr.png")
def card_qr_image(card_id: int):
    """Serves the QR image for a freshly-issued card. Only reachable via
    the one-time link shown right after registration or PIN retrieval --
    there is no index/listing of card ids.
    """
    card = db.session.get(Card, card_id) or abort(404)
    if not card.active:
        abort(404)
    png_bytes = token_to_qr_png_bytes(card.token)
    return Response(png_bytes, mimetype="image/png")


@card_bp.route("/card/retrieve", methods=["GET", "POST"])
@csrf.exempt  # plain HTML form, no session/CSRF cookie assumed on a shared kiosk browser
@limiter.limit("10 per minute")
def retrieve_card():
    """Lets a member re-view their QR gårdskort using their name + PIN,
    in case the original screenshot was lost. Intended to be used over
    the Raspberry Pi's own local Wi-Fi access point.
    """
    qr_url = None
    member_name = None
    if request.method == "POST":
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        pin = (request.form.get("pin") or "").strip()

        candidates = Member.query.filter_by(
            first_name=first_name, last_name=last_name, active=True
        ).all()
        match = next((m for m in candidates if m.check_retrieval_pin(pin)), None)

        if match is None:
            flash("Namn eller PIN-kod stämmer inte.", "danger")
        else:
            card = match.active_card()
            if card is None:
                flash("Inget aktivt kort hittades. Be personalen utfärda ett nytt.", "warning")
            else:
                db.session.add(LogEntry(event_type="card_retrieval", member_id=match.id, source="web-app"))
                db.session.commit()
                qr_url = f"/card/{card.id}/qr.png"
                member_name = match.full_name()

    return render_template("card/retrieve.html", qr_url=qr_url, member_name=member_name)


@card_bp.route("/gate/scan", methods=["POST"])
@csrf.exempt  # called by the kiosk JS and by the external camera-fallback script
@limiter.limit("120 per minute")
def gate_scan():
    """Ingest endpoint for the gate scanner. A USB HID barcode scanner
    "types" the decoded token into a focused text field; the kiosk page's
    JS submits that via fetch() to this endpoint (see
    templates/gate/scan_kiosk.html). The optional camera-based fallback
    (scanner/camera_scan.py) POSTs here too. Always responds with JSON so
    both callers can render the result without a page reload.
    """
    token = request.form.get("token") or request.values.get("token")
    result = process_gate_scan(token, source=request.form.get("source", "gate-scanner"))
    return jsonify(
        {
            "status": result.status,
            "message": result.message,
            "member_name": result.member.full_name() if result.member else None,
        }
    )


@card_bp.route("/gate")
def gate_kiosk():
    return render_template("gate/scan_kiosk.html")
