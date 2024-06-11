from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import DateTimeField, SelectField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, NumberRange, Optional
import sqlalchemy as sa
from app.factory import db
from app.models import User, GidGud, Category
from flask import current_app, request


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('An account with this Username already exists. Please choose a different Username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('An account with this email address already exists. Please choose a different email address.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit!')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == self.username.data))
            if user is not None:
                raise ValidationError('An account with this email address already exists. Please choose a different email address.')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class GidGudForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    rec_instant = BooleanField('Repeat Task')
    rec_custom = SubmitField('Custom Schedule')
    rec_val = IntegerField('Frequency', validators=[Optional(), NumberRange(min=0, max=999999)])
    rec_unit = SelectField('TimeUnit', choices=['days', 'weeks', 'months', 'years', 'hours', 'minutes', 'instantly'], validators=[Optional()])
    submit = SubmitField('Submit')

class GidGudForm2(FlaskForm):
    body = StringField('GidGud', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    rec_instant = BooleanField('Always Repeat')
    change_view = SubmitField()
    rec_custom = BooleanField('Custom Schedule')
    rec_val = IntegerField('Timer Frequency', validators=[Optional(), NumberRange(min=0, max=999999)])
    rec_unit = SelectField('TimeUnit', choices=['days', 'weeks', 'months', 'years', 'hours', 'minutes'], validators=[Optional()])
    # TODO: implement rec_next as 'Start at' with iso_now default in create route and 'Sleep until' with current value in edit route
    # rec_next = DateTimeField('Date and Time', format='%d/%m/%Y %H:%M', validators=[DataRequired()])
    # route GET - form.datetime.data = datetime.now().replace(second=0, microsecond=0)
    # Template - <p>{{ form.datetime.label }}<br> <input type="datetime-local" name="datetime" value="{{ form.datetime.data.strftime('%Y-%m-%dT%H:%M') }}"></p>
    reset_timer = BooleanField('Start Now')
    submit = SubmitField('Submit')

    def validate_rec_instant(self, rec_instant, rec_custom):
        if rec_instant.data and rec_custom.data:
            raise ValidationError('Please choose either <Always Repeat> or <Custom Schedule>')

class EditGidGudForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    rec_val = IntegerField('Repeat after', validators=[NumberRange(min=0)], default=0)
    rec_unit = SelectField('TimeUnit', choices=['instantly', 'days', 'weeks', 'months', 'hours', 'minutes'])
    submit = SubmitField('Change GidGud')

    def validate_rec_unit(self, rec_unit):
        if self.rec_val.data > 1 and rec_unit.data == 'instantly':
            raise ValidationError('Please choose a time unit for recurrence.')
        if self.rec_val.data == 0 and rec_unit.data != 'instantly':
            raise ValidationError(f'Please fill out Repeat after or set TimeUnit to None.')

class CreateGidForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    rec_val = IntegerField('Repeat after', validators=[NumberRange(min=0)], default=0)
    rec_unit = SelectField('TimeUnit', choices=['instantly', 'days', 'weeks', 'months', 'hours', 'minutes'])
    submit = SubmitField('Create Gid')

    def validate_rec_unit(self, rec_unit):
        if self.rec_val.data > 1 and rec_unit.data == 'instantly':
            raise ValidationError('Please choose a TimeUnit for recurrence.')
        if self.rec_val.data == 0 and rec_unit.data != 'instantly':
            raise ValidationError(f'Please fill out Repeat after or set TimeUnit to None.')

class CreateGudForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    submit = SubmitField('Create Gud')

class CreateCategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=20)])
    submit = SubmitField('Create Category')

    def validate_name(self, name):
        category = db.session.scalar(sa.select(Category).where(Category.name == name.data))
        if category is not None:
            raise ValidationError('This category already exists.')
        if name.data.lower() in ["root", "default", "none", "null", "0", "no parent", "no children", "no gidguds", "remove"]:
            raise ValidationError('This name is not valid.')

class EditCategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=20)])
    parent = SelectField('New Parent:')
    reassign_gidguds = SelectField('Reassign GidGuds to:')
    reassign_children = SelectField('Reassign children to:')
    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        self.current_name = kwargs.pop('current_name', None)
        super(EditCategoryForm, self).__init__(*args, **kwargs)

    def validate_name(self, name):
        if name.data == self.current_name:
            return  # Skip validation if the submitted name matches the current name

        category = db.session.scalar(sa.select(Category).where(Category.name == name.data))
        if category is not None:
            raise ValidationError('This category already exists.')
        if name.data.lower() in ["root", "default", "none", "null", "0", "no parent", "no children", "no gidguds", "remove"]:
            raise ValidationError('This name is not valid.')
