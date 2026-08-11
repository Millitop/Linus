from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional


class RegisterChildForm(FlaskForm):
    first_name = StringField("Förnamn", validators=[DataRequired()])
    last_name = StringField("Efternamn", validators=[DataRequired()])
    group_class = StringField("Grupp/klass", validators=[Optional()])
    birth_year = IntegerField("Födelseår (valfritt)", validators=[Optional()])

    guardian_name = StringField("Vårdnadshavarens namn", validators=[DataRequired()])
    guardian_phone = StringField("Telefon", validators=[Optional()])
    guardian_email = StringField("E-post", validators=[Optional()])

    submit = SubmitField("Registrera och skapa gårdskort")


class ManualAttendanceForm(FlaskForm):
    submit = SubmitField("Rätta status")
