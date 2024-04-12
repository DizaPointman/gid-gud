from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateGidGudForm, EditGidGudForm, CreateCategoryForm, EditCategoryForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, GidGud, Category
from app.utils import category_child_protection_service, category_handle_change_parent, category_handle_reassign_gidguds, category_handle_rename, check_and_return_list_of_possible_parents, check_and_return_list_of_possible_parents_for_children, check_if_category_exists_and_return, create_new_category
from urllib.parse import urlsplit
from datetime import datetime, timezone


@app.route('/')
@app.route('/index')
@login_required
def index():
    gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
    return render_template('index.html', title='Home', gidguds=gidguds)

@app.route('/login', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            app.logger.info('%s tried logging in with invalid username or password', user.username)
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        app.logger.info('%s logged in successfully', user.username)
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/create_gidgud', methods=['GET', 'POST'])
@login_required
def create_gidgud():
    form = CreateGidGudForm()
    gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
    if form.validate_on_submit():
        category = check_if_category_exists_and_return(form.category.data)
        if not category:
            new_category = Category(name=form.category.data, user_id=current_user.id)
            db.session.add(new_category)
            category = new_category
        gidgud = GidGud(body=form.body.data, user_id=current_user.id, recurrence=form.recurrence.data, recurrence_rhythm=form.recurrence_rhythm.data, category=category)
        db.session.add(gidgud)
        db.session.commit()
        flash('New GidGud created!')
        return redirect(url_for('index'))
    return render_template('create_gidgud.html', title='Create GidGud', form=form, gidguds=gidguds)

@app.route('/edit_gidgud/<id>', methods=['GET', 'POST'])
@login_required
def edit_gidgud(id):
    gidgud = db.session.scalar(sa.select(GidGud).where(id == GidGud.id))
    form = EditGidGudForm()
    if form.validate_on_submit():
        gidgud.body = form.body.data
        gidgud.recurrence = form.recurrence.data
        gidgud.recurrence_rhythm = form.recurrence_rhythm.data
        if form.category.data is not gidgud.category.name:
            updated_category = check_if_category_exists_and_return(form.category.data)
            if not updated_category:
                new_category = Category(name=form.category.data, user_id=current_user.id)
                db.session.add(new_category)
                gidgud.category = new_category
            else:
                gidgud.category = updated_category
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.body.data = gidgud.body
        form.recurrence.data = gidgud.recurrence
        form.recurrence_rhythm.data = gidgud.recurrence_rhythm
        form.category.data = gidgud.category.name
    return render_template('edit_gidgud.html', title='Edit GidGud', form=form)

@app.route('/delete_gidgud/<id>', methods=['GET', 'DELETE', 'POST'])
@login_required
def delete_gidgud(id):
    current_gidgud = db.session.scalar(sa.select(GidGud).where(id == GidGud.id))
    db.session.delete(current_gidgud)
    db.session.commit()
    flash('GidGud deleted!')
    return redirect(url_for('index'))

@app.route('/complete_gidgud/<id>', methods=['GET', 'POST'])
@login_required
def complete_gidgud(id):
    current_gidgud = db.session.scalar(sa.select(GidGud).where(id == GidGud.id))
    current_gidgud.completed = True
    db.session.commit()
    flash('GidGud completed!')
    return redirect(url_for('index'))

@app.route('/user/<username>/user_categories', methods=['GET'])
@login_required
def user_categories(username):
    categories = db.session.scalars(sa.select(Category).where(current_user == Category.user))
    return render_template('user_categories.html', title='My Categories', categories=categories)

@app.route('/create_category', methods=['GET', 'POST'])
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
        new_category_name = form.name.data
        create_new_category(new_category_name, current_user.id)
        flash('New Category created!')
        return redirect(url_for('user_categories', username=current_user.username))

    return render_template('create_category.html', title='Create Category', form=form, categories=categories)

@app.route('/edit_category/<id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    # TODO: update delete_afterwards interpreter
    # TODO: change choices to exclude the current category on deletion
    # TODO: add multiple children at once

    current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
    app.logger.info(f'Starting the edit_category route for category id: {id}, name: {current_category.name}')
    #delete_afterwards = request.args.get('delete_afterwards', 'False') == 'True'
    dla = request.args.get('dla') or {}
    delete_afterwards = bool(dla)
    #if not dla:
        #dla = {}
    app.logger.info(f'dla on start of edit route: {dla}')
    app.logger.info(f'delete_afterwards: {delete_afterwards}')

    app.logger.info(f'category to edit: {current_category.name}, id: {current_category.id}, parent: {current_category.parent}, children: {current_category.children}')


    # Choices: all categories except the current category
    gidgud_reassignment_choices = [current_category.name] + [category.name for category in current_user.categories if category != current_category]

    default_parent_choices = [current_category.parent.name] + ['No Parent'] if current_category.parent else ['No Parent']
    parent_choices = default_parent_choices + check_and_return_list_of_possible_parents(current_category)

    default_parent_choices_for_children = ['No Children']
    parent_choices_for_children = check_and_return_list_of_possible_parents_for_children(current_category) or default_parent_choices_for_children

    form = EditCategoryForm()
    # Assigning choices to selection fields
    form.parent.choices = parent_choices
    form.reassign_gidguds.choices = gidgud_reassignment_choices
    form.reassign_children.choices = parent_choices_for_children

    if form.validate_on_submit():


        # Check if form contains new parent
        if form.parent.data != ('No Parent' if current_category.parent is None else current_category.parent.name):
            app.logger.info(f'calling parent change: old:{current_category.parent}, new: {form.parent.data}')
            # Assign new parent
            category_handle_change_parent(current_category, form)

        # Check if form contains new category for gidguds
        if form.reassign_gidguds.data != current_category.name:
            app.logger.info(f'calling reassign gidguds: old:{current_category.name}, new: {form.reassign_gidguds.data}')
            # Assign gidguds to new category
            category_handle_reassign_gidguds(current_category, form)

        # Check if form contains a new parent category for the current category's children
        if form.reassign_children.data not in (default_parent_choices_for_children, current_category.name, 'No Children'):
            # Assign children categories to the new parent category
            category_child_protection_service(current_category, form)

        # Check if form contains new category name
        if form.name.data != current_category.name:
            app.logger.info(f'calling name change: old:{current_category.name}, new {form.name.data}')
            # Assign new category name
            category_handle_rename(current_category, form)

        #if delete_afterwards:
        if delete_afterwards:
            app.logger.info(f'This shows up if we reach the delete afterwards statement in edit: {dla}')
            return redirect(url_for('delete_category', username=current_user.username, id=id))
        return redirect(url_for('user_categories', username=current_user.username))

    elif request.method == 'GET':
        # populating fields for get requests
        form.name.data = current_category.name
        form.parent.choices = parent_choices
        form.reassign_gidguds.choices = gidgud_reassignment_choices
        form.reassign_children.choices = parent_choices_for_children

    return render_template('edit_category.html', title='Edit Category', id=id, form=form, dla=dla)

@app.route('/delete_category/<id>', methods=['GET', 'DELETE', 'POST'])
@login_required
def delete_category(id):
    # TODO: create function that creates dict based on necessity of edit before delete
    # TODO: pass the dict in a way the edit template can interpret and adapt to display only necessary form fields
    # TODO: simplify delete_afterwards parameter
    current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
    dla = {}
    if current_category.gidguds: dla['g']=True
    if current_category.children: dla['c']=True
    app.logger.info(f'dla before passing to edit route: {dla}')
    #delete_afterwards = True
    if current_category.name == 'default':
        flash('The default Category may not be deleted')
        return redirect(url_for('user_categories', username=current_user.username))
    #elif current_category.gidguds or current_category.children:
    #    flash('This Category has attached GidGuds or Subcategories. Please reassign before deletion.')
    #    return redirect(url_for('edit_category', id=id, delete_afterwards=delete_afterwards))
    elif dla:
        flash('This Category has attached GidGuds or Subcategories. Please reassign before deletion.')
        return redirect(url_for('edit_category', id=id, dla=dla))
    else:
        db.session.delete(current_category)
        db.session.commit()
        flash('Category deleted!')
    return redirect(url_for('user_categories', username=current_user.username))

@app.route('/user/<username>/statistics', methods=['GET'])
@login_required
def statistics(username):
    gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
    return render_template('statistics.html', title='My Statistic', gidguds=gidguds)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
    return render_template('user.html', user=user, gidguds=gidguds)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()