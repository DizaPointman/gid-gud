from flask import Blueprint, current_app, render_template, flash, redirect, session, url_for, request
from app.factory import db
from app.forms import CreateGidForm, CreateGudForm, EmptyForm, GidGudForm, LoginForm, RegistrationForm, EditProfileForm, EditGidGudForm, CreateCategoryForm, EditCategoryForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.managers.content_manager import ContentManager
from app.models import User, GidGud, Category
from app.utils import log_exception, log_form_validation_errors, log_object, log_request
from urllib.parse import urlsplit
from datetime import datetime, timezone
from pytz import utc
from werkzeug.datastructures import MultiDict


# Create Blueprint
bp = Blueprint('routes', __name__)

# Initialize ContentManager
c_man = ContentManager()


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    c_man.test_cm()
    gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
    return render_template('index.html', title='Home', gidguds=gidguds)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    The `login` function in this Python code handles user authentication and login functionality,
    including form validation, logging in the user, and redirecting to the appropriate page.
    :return: The code snippet provided is a Flask route for handling user login functionality. When a
    user accesses the '/login' route, the function checks if the current user is already authenticated.
    If the user is authenticated, it redirects to the 'index' page. If not, it renders a login form
    using the 'LoginForm' class.
    """
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            current_app.logger.info('%s tried logging in with invalid username or password', user.username)
            flash('Invalid username or password')
            return redirect(url_for('routes.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('routes.index')
        current_app.logger.info('%s logged in successfully', user.username)
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = RegistrationForm()
    if form.validate_on_submit():

        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('routes.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('routes.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('routes.index'))
        if user == current_user:
            flash('You cannot follow yourself you fucking narcissist!')
            return redirect(url_for('routes.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('routes.user', username=username))
    else:
        return redirect(url_for('index'))

@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('routes.index'))
        if user == current_user:
            flash('You cannot unfollow yourself you fucking narcissist!')
            return redirect(url_for('routes.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username} anymore.')
        return redirect(url_for('routes.user', username=username))
    else:
        return redirect(url_for('routes.index'))

@bp.route('/create_gidgud', methods=['GET', 'POST'])
@login_required
def create_gidgud():
    title = 'New GidGud'

    customize = request.args.get('customize', 'false') == 'true'

    # Prepopulate form data from the session
    if 'form_data' in session:
        form = GidGudForm(data=session['form_data'])
    else:
        form = GidGudForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Save form data to the session
            session['form_data'] = {
                'body': form.body.data,
                'category': form.category.data,
                'rec_instant': form.rec_instant.data
            }
            if form.rec_custom.data:
                new_customize_state = 'false' if customize else 'true'
                return redirect(url_for('routes.create_gidgud', customize=new_customize_state, title=title))

            elif form.submit.data:
                gg = c_man.gidgud_create_from_form(form)
                flash('New Gid created!')
                session.pop('form_data', None)  # Clear form data from the session after successful submit
                return redirect(url_for('routes.index'))

    return render_template('create_or_edit_gidgud.html', title=title, form=form, customize=customize)

@bp.route('/edit_gidgud/<id>', methods=['GET', 'POST'])
@login_required
def edit_gidgud(id):

    # TODO: better display difference between instantly and the rest of repetition, remove repetition with checkbox

    title = 'Edit GidGud'
    gidgud = db.session.scalar(sa.select(GidGud).where(id == GidGud.id))
    customize = request.args.get('customize', 'false') == 'true'
    if gidgud.rec_val != 0:
        customize = 'true'

    # Prepopulate form data from the session
    if 'form_data' in session:
        form = GidGudForm(data=session['form_data'])
    else:
        form = GidGudForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Save form data to the session
            session['form_data'] = {
                'body': form.body.data,
                'category': form.category.data,
                'rec_instant': form.rec_instant.data
            }
            if form.rec_custom.data:
                new_customize_state = 'false' if customize else 'true'
                return redirect(url_for('routes.edit_gidgud', customize=new_customize_state, title=title, id=id))

            elif form.submit.data:

                c_man.gidgud_update_from_form(gidgud.id, form)
                db.session.commit()

                flash('GidGud successful edited!')
                session.pop('form_data', None)  # Clear form data from the session after successful submit
                return redirect(url_for('routes.index'))

    elif request.method == 'GET':
        form.body.data = gidgud.body
        form.category.data = gidgud.category.name
        if gidgud.rec_val != 0:
            form.rec_val.data = gidgud.rec_val
            form.rec_unit.data = gidgud.rec_unit

    return render_template('create_or_edit_gidgud.html', title=title, form=form, customize=customize)

@bp.route('/create_gid', methods=['GET', 'POST'])
@login_required
def create_gid():
    gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
    form = CreateGidForm()
    # TODO: create flash that informs about recurrence rhythm
    if form.validate_on_submit():
        category = c_man.return_or_create_category(name=(form.category.data))
        if form.rec_val.data != 0:
            gid = GidGud(body=form.body.data, user_id=current_user.id, category=category, rec_val=form.rec_val.data, rec_unit=form.rec_unit.data)
        else:
            gid = GidGud(body=form.body.data, user_id=current_user.id, category=category)
        db.session.add(gid)
        db.session.commit()
        flash('New Gid created!')
        return redirect(url_for('routes.index'))
    return render_template('create_gid.html', title='Create Gid', form=form, gidguds=gidguds)

@bp.route('/create_gud', methods=['GET', 'POST'])
@login_required
def create_gud():
    gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
    form = CreateGudForm()
    if form.validate_on_submit():
        category = c_man.return_or_create_category(name=(form.category.data))
        timestamp = datetime.now(timezone.utc)
        gud = GidGud(body=form.body.data, user_id=current_user.id, category=category, completed_at=timestamp)
        db.session.add(gud)
        db.session.commit()
        flash('New Gud created!')
        return redirect(url_for('routes.index'))
    return render_template('create_gud.html', title='Create Gud', form=form, gidguds=gidguds)

"""
@bp.route('/edit_gidgud/<id>', methods=['GET', 'POST'])
@login_required
def edit_gidgud(id):
    gidgud = db.session.scalar(sa.select(GidGud).where(id == GidGud.id))
    # TODO: adjust template to hide recurrence fields when editing completed_at gidgud
    form = EditGidGudForm()
    if form.validate_on_submit():
        c_man.gidgud_handle_update(gidgud, form)
        flash('Your changes have been saved.')
        return redirect(url_for('routes.index'))

    elif request.method == 'GET':
        form.body.data = gidgud.body
        form.category.data = gidgud.category.name
        form.rec_val.data = gidgud.rec_val
        form.rec_unit.data = gidgud.rec_unit

    return render_template('edit_gidgud.html', title='Edit GidGud', form=form)
"""

@bp.route('/delete_gidgud/<id>', methods=['GET', 'DELETE', 'POST'])
@login_required
def delete_gidgud(id):
    current_gidgud = db.session.scalar(sa.select(GidGud).where(id == GidGud.id))
    db.session.delete(current_gidgud)
    db.session.commit()
    flash('GidGud deleted!')
    return redirect(url_for('routes.index'))

@bp.route('/complete_gidgud/<id>', methods=['GET', 'POST'])
@login_required
def complete_gidgud(id):
    # TODO: make recurrence = 1 and timeunit=None instant recurrence
    current_gidgud = db.session.scalar(sa.select(GidGud).where(id == GidGud.id))
    c_man.gidgud_handle_complete(current_gidgud)
    flash('Gid completed_at!')
    return redirect(url_for('routes.index'))

@bp.route('/user/<username>/user_categories', methods=['GET'])
@login_required
def user_categories(username):
    categories = db.session.scalars(sa.select(Category).where(current_user == Category.user))
    return render_template('user_categories.html', title='My Categories', categories=categories)

@bp.route('/create_category', methods=['GET', 'POST'])
@login_required
def create_category():
    """
    Handle requests to create a new category.

    GET: Display the form to create a new category.
    POST: Process the form submission to create a new category.

    Returns:
        flask.Response: Redirects to the user's categories page upon successful creation.
    """
    form = CreateCategoryForm()
    categories = db.session.scalars(sa.select(Category).where(current_user == Category.user))

    if form.validate_on_submit():
        category = c_man.create_category_from_form(form)
        flash('New Category created!')
        return redirect(url_for('routes.user_categories', username=current_user.username))

    return render_template('create_category.html', title='Create Category', form=form, categories=categories)

@bp.route('/edit_category/<id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    # TODO: add multiple children at once

    current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
    delete_afterwards = bool(request.args.get('dla'))

    # Choices: all categories except the current category

    parent_choices = [current_category.parent.name or current_category.name] + c_man.get_possible_parents(current_category)

    if current_category.gidguds:
        gidgud_reassignment_choices = [current_category.name, 'root'] + [c.name for c in current_user.categories if c.name not in [current_category.name, 'root']]
    else:
        gidgud_reassignment_choices = ['No GidGuds']

    if current_category.children:
        parent_choices_for_children = [current_category.name] + c_man.get_possible_parents_for_children(current_category)
    else:
        parent_choices_for_children = ['No Children']

    form = EditCategoryForm(current_name=current_category.name)

    # Assigning choices to selection fields
    form.parent.choices = parent_choices
    form.reassign_gidguds.choices = gidgud_reassignment_choices
    form.reassign_children.choices = parent_choices_for_children

    if request.method == 'POST':

        if form.validate_on_submit():

            c_man.update_category_from_form(id, form)

            #if delete_afterwards:
            if delete_afterwards:
                return redirect(url_for('routes.delete_category', username=current_user.username, id=id))
            return redirect(url_for('routes.user_categories', username=current_user.username))

        else:
            # Form validation failed, render the form template again with error messages
            log_form_validation_errors(form)
            flash('Form validation failed. Please correct the errors and resubmit.')
            return render_template('edit_category.html', title='Edit Category', id=id, form=form, cat=current_category, dla=delete_afterwards)

    elif request.method == 'GET':
        # populating fields for get requests
        form.name.data = current_category.name
        form.parent.choices = parent_choices
        form.reassign_gidguds.choices = gidgud_reassignment_choices
        form.reassign_children.choices = parent_choices_for_children

    return render_template('edit_category.html', title='Edit Category', id=id, form=form, cat=current_category, dla=delete_afterwards)

@bp.route('/delete_category/<id>', methods=['GET', 'DELETE', 'POST'])
@login_required
def delete_category(id):
    current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
    if current_category.name == 'root':
        flash('The root Category may not be deleted')
        return redirect(url_for('routes.user_categories', username=current_user.username))
    elif current_category.gidguds or current_category.children:
        flash('This Category has attached GidGuds or Subcategories. Please reassign before deletion.')
        return redirect(url_for('routes.edit_category', id=id, dla=True))
    else:
        db.session.delete(current_category)
        db.session.commit()
        flash('Category deleted!')
    return redirect(url_for('routes.user_categories', username=current_user.username))

@bp.route('/user/<username>/statistics', methods=['GET'])
@login_required
def statistics(username):

    possible_choices = ['all', 'gids', 'sleep', 'guds']
    gidguds = c_man.gidgud_return_dict_from_choice(['gids', 'sleep', 'guds'])
    current_app.logger.info(f"{gidguds}")

    return render_template('statistics.html', title='My Statistic', gidguds=gidguds)

@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
    form = EmptyForm()
    return render_template('user.html', user=user, gidguds=gidguds, form=form)

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()