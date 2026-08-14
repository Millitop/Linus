from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Optional


class RegisterMemberForm(FlaskForm):
    """Staff-assisted registration, e.g. helping someone whose phone is
    broken. The public self-registration flow at /join uses the same
    register_member() service directly without this form (no staff
    session there).
    """

    first_name = StringField("Förnamn", validators=[DataRequired()])
    last_name = StringField("Efternamn", validators=[DataRequired()])
    phone = StringField("Telefon (valfritt)", validators=[Optional()])

    submit = SubmitField("Registrera och skapa gårdskort")


class EditMemberForm(FlaskForm):
    first_name = StringField("Förnamn", validators=[DataRequired()])
    last_name = StringField("Efternamn", validators=[DataRequired()])
    phone = StringField("Telefon (valfritt)", validators=[Optional()])

    submit = SubmitField("Spara ändringar")


class MemberSearchForm(FlaskForm):
    query = StringField("Sök på namn", validators=[DataRequired()])
    submit = SubmitField("Sök")


class ManualAttendanceForm(FlaskForm):
    submit = SubmitField("Rätta status")
