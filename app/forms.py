from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
import re
#from flask_pagedown.fields import PageDownField
#from ..models import Clinic, Search

def length_check(FlaskForm, field):
    if len(field.data) != 6:
        raise ValidationError('You postal code is not equal to 6 digits.')

def numbers_check(FlaskForm, field):
    check = bool(re.match(r"^[0-9]*$", field.data))
    if check == False:
        raise ValidationError('Please remove characters from your postal code.')

class ClinicForm(FlaskForm):
    postal_code = StringField('Please enter your postal code here:', [DataRequired(), length_check,numbers_check])
    submit = SubmitField('Submit')
