from flask import Blueprint, current_app, render_template, flash, redirect, session, url_for, request
from app.factory import db
from app.forms import EmptyForm, GidGudForm, LoginForm, RegistrationForm, EditProfileForm, CreateCategoryForm, EditCategoryForm
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

    view = request.args.get('view', 'simple')
    form = GidGudForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Save form data to the session
            session['form_data'] = {
                'body': form.body.data,
                'category': form.category.data,
                'rec_instant': form.rec_instant.data or form.rec_instant.default,
                'rec_custom': form.rec_custom.data or form.rec_custom.default,
                'reset_timer': form.reset_timer.data or form.reset_timer.default
            }
            if form.change_view.data:
                # Preserve data and change view
                view = 'advanced' if view == 'simple' else 'simple'
                return redirect(url_for('routes.create_gidgud', view=view, title=title))

            elif form.submit.data:
                gidgud = c_man.gidgud_create_from_form(form)
                if gidgud:
                    flash('New Gid created!')
                    session.pop('form_data', None)
                    return redirect(url_for('routes.index'))
                else:
                    flash('Error creating new Gid.', 'error')

    elif request.method == 'GET':
        form.reset_timer.data = form.reset_timer.default
        form.rec_custom.data = form.rec_custom.default
        form.rec_instant.data = form.rec_instant.default

    # Populate form with default values or session data if available
    fields = form._fields.keys()
    if 'form_data' in session:
        c_man.populate_form(form, session['form_data'], fields)

    return render_template('create_or_edit_gidgud.html', title=title, form=form, view=view)

@bp.route('/edit_gidgud/<id>', methods=['GET', 'POST'])
@login_required
def edit_gidgud(id):
    view = request.args.get('view', 'simple')
    title = 'Edit GidGud'
    form = GidGudForm()

    gidgud = db.session.scalar(sa.select(GidGud).where(GidGud.id == id))

    if form.validate_on_submit():
        if form.change_view.data:
            # Preserve data and change view
            session['form_data'] = {field: getattr(form, field).data for field in form._fields}
            view = 'advanced' if view == 'simple' else 'simple'
            return redirect(url_for('edit_gidgud', id=id, view=view, title=title))

        if form.submit.data:
            """
            # Handle form submission
            gidgud.body = form.body.data
            gidgud.category = form.category.data
            gidgud.rec_val = form.rec_val.data if form.rec_val.data is not None else None
            gidgud.rec_unit = form.rec_unit.data if form.rec_unit.data != 'None' else None
            gidgud.rec_next = form.rec_next.data.isoformat()
            gidgud.reset_timer = form.reset_timer.data

            # Determine rec_instant and rec_custom values based on rec_val and rec_unit
            if gidgud.rec_val is None and gidgud.rec_unit is None:
                gidgud.rec_instant = False
                gidgud.rec_custom = False
            elif gidgud.rec_val == 0 and gidgud.rec_unit is not None:
                gidgud.rec_instant = True
                gidgud.rec_custom = False
            elif gidgud.rec_val > 0 and gidgud.rec_unit is not None:
                gidgud.rec_instant = False
                gidgud.rec_custom = True
            """
            gg = c_man.gidgud_update_from_form(id, form)

            flash('Form submitted successfully!', 'success')
            session.pop('form_data', None)  # Clear form data from session after submission
            return redirect(url_for('index'))  # Assume you have a success page

    # Populate form with default values or session data if available
    fields = form._fields.keys()
    if 'form_data' in session:
        c_man.populate_form(form, session['form_data'], fields)
    else:
        gidgud_data = {
            'body': gidgud.body,
            'category': gidgud.category,
            'rec_instant': gidgud.rec_instant,
            'rec_custom': gidgud.rec_custom,
            'rec_val': gidgud.rec_val if gidgud.rec_val is not None else None,
            'rec_unit': gidgud.rec_unit if gidgud.rec_unit is not None else 'None',
            'rec_next': datetime.fromisoformat(gidgud.rec_next),
            'reset_timer': gidgud.reset_timer
        }
        c_man.populate_form(form, gidgud_data, fields)

    return render_template('create_or_edit_gidgud.html', form=form, view=view, title=title)

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