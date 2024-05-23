from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, NumberRange, Optional
import sqlalchemy as sa
from app import db
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
            raise ValidationError('Please choose a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Please choose a different email address.')

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
                raise ValidationError('Please use a different username.')
            
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class EditGidGudForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    rec_rhythm = IntegerField('Repeat after', validators=[NumberRange(min=0)], default=0)
    time_unit = SelectField('TimeUnit', choices=['None', 'days', 'weeks', 'months', 'hours', 'minutes'])
    submit = SubmitField('Change GidGud')

    def validate_time_unit(self, time_unit):
        if self.rec_rhythm.data != 0 and time_unit.data == 'None':
            raise ValidationError('Please choose a time unit for recurrence.')
        if self.rec_rhythm.data == 0 and time_unit.data != 'None':
            raise ValidationError(f'Please fill out Repeat after or set TimeUnit to None.')

class CreateGidForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    rec_rhythm = IntegerField('Repeat after', validators=[NumberRange(min=0)], default=0)
    time_unit = SelectField('TimeUnit', choices=['None', 'days', 'weeks', 'months', 'hours', 'minutes'])
    submit = SubmitField('Create Gid')

    def validate_time_unit(self, time_unit):
        if self.rec_rhythm.data > 1 and time_unit.data == 'None':
            raise ValidationError('Please choose a time unit for recurrence.')
        if self.rec_rhythm.data == 0 and time_unit.data != 'None':
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
        if name.data.lower() in ["root", "none", "null", "0", "no parent", "no children", "no gidguds", "remove"]:
            raise ValidationError('This name is not valid.')

class EditCategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=20)])
    parent = SelectField('New Parent:')
    reassign_gidguds = SelectField('Reassign GidGuds to:')
    reassign_children = SelectField('Reassign children to:')
    submit = SubmitField('Save Changes')

    def validate_name(self, name):
        category = db.session.scalar(sa.select(Category).where(Category.name == name.data))
        if category is not None:
            raise ValidationError('This category already exists.')
        if name.data.lower() in ["root", "none", "null", "0", "no parent", "no children", "no gidguds", "remove"]:
            raise ValidationError('This name is not valid.')
