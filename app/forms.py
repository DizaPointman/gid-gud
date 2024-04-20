import traceback
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, NumberRange, InputRequired, Optional
from wtforms.widgets import TextInput
import sqlalchemy as sa
from app import db
from app.models import User, GidGud, Category
from flask import current_app, request
from markupsafe import Markup


class HTMLString(str):
    #A string class that escapes HTML by default.
    def __html__(self):
        #Return the string as its escaped HTML representation.
        return self
class DatalistInput(TextInput):
    """
    Custom widget to create an input with a datalist attribute
    """

    def __init__(self, datalist=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datalist = datalist or []

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)

        html = [f'<input list="{field.id}_list" id="{field.id}" name="{field.name}">']
        html.append(f'<datalist id="{field.id}_list">')

        for item in field.datalist:
            html.append(f'<option value="{item}">')

        html.append('</datalist>')

        return HTMLString(''.join(html))

class DatalistField(StringField):
    """
    Custom field type for datalist input
    """
    widget = DatalistInput()

    def __init__(self, label=None, datalist=None, **kwargs):
        super().__init__(label, **kwargs)
        self.datalist = datalist or []

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]
        else:
            self.data = None

class DataStringField(StringField):
    def __init__(self, choices=(), **kwargs):
        try:
            super().__init__(**kwargs)
            self.choices = choices
            self.render_kw = {}  # Initialize render_kw as an empty dictionary

            if choices:
                self.render_kw.setdefault('list', self.id + "_datalist")
        except:
            traceback.print_exc()

    def __call__(self, **kwargs):
        try:
            res = super().__call__(**kwargs)

            if datalist_id := self.render_kw.get('list'):
                html_list = [f'<datalist id="{datalist_id}">']
                for choice in self.choices:
                    html_list.append(f"<option value=\"{choice}\"/>")
                html_list.append("</datalist>")
                datalist_html = Markup("\n".join(html_list))
                return res + datalist_html
            else:
                return res
        except:
            traceback.print_exc()

# Function to get choices
def get_category_choices():
    # Implement logic to retrieve categories, for example:
    # Assuming current_user is available and authenticated
    if current_user.is_authenticated:
        return [category.name for category in current_user.categories]
    else:
        return []

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

class CreateGidGudForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    submit = SubmitField('Create GidGud')

class EditGidGudForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    submit = SubmitField('Change GidGud')

class CreateGidForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = StringField('Category', validators=[Length(max=20)])
    rec_rhythm = IntegerField('Repeat after', validators=[NumberRange(min=0)], default=0)
    time_unit = SelectField('TimeUnit', choices=['', 'days', 'weeks', 'months', 'hours', 'minutes'])
    submit = SubmitField('Create Gid')

    def validate_time_unit(self, time_unit):
        if self.rec_rhythm.data != 0 and not time_unit.data:
            raise ValidationError('Please choose a time unit for recurrence.')
        if self.rec_rhythm.data == 0 and time_unit.data:
            raise ValidationError(f'Please fill out Repeat after or remove TimeUnit.')

class CreateGudForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    #category = DataStringField('Category')
    category = DatalistField('Category')
    submit = SubmitField('Create Gud')

    def __init__(self, *args, **kwargs):
        super(CreateGudForm, self).__init__(*args, **kwargs)
        # Initialize category choices using the function
        self.category.datalist = get_category_choices()

    """def __init__(self, *args, **kwargs):
        super(CreateGudForm, self).__init__(*args, **kwargs)
        # Initialize category choices using the function
        self.category.choices = get_category_choices()"""

class CreateCategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=20)])
    submit = SubmitField('Create Category')

    def validate_name(self, name):
        category = db.session.scalar(sa.select(Category).where(Category.name == name.data))
        if category is not None:
            raise ValidationError('This category already exists.')

class EditCategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=20)])
    parent = SelectField('New Parent:')
    reassign_gidguds = SelectField('Reassign GidGuds to:')
    reassign_children = SelectField('Reassign children to:')
    submit = SubmitField('Save Changes')

