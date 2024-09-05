from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, EmailField, PasswordField, SubmitField,IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional


class ContactSalesForm(FlaskForm):
    fname = StringField(validators=[Length(2, 50), Optional()])
    sname = StringField(validators=[Length(2, 50), Optional()])
    email = EmailField(validators=[DataRequired(), Length(4, 50)])
    phone = StringField(validators=[Length(11, 11), Optional()])
    company_link = StringField(validators=[Length(11), Optional()])
    title = StringField(validators=[Length(1, 20), Optional()])
    no_employees = IntegerField(validators=[Length(min=0), Optional()])
