from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import CreateCategoryForm, LoginForm, RegistrationForm, EditProfileForm, CreateGidGudForm, EditGidGudForm, EditCategoryForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, GidGud, Category
from app.utils import check_if_category_exists_and_return_or_false, create_new_category, check_if_category_has_gidguds_and_return_list, handle_name_change, handle_reassign_gidguds, update_gidgud_category
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
        category = check_if_category_exists_and_return_or_false(current_user, form.category.data)
        if not category:
            category = create_new_category(current_user, form.category.data)
            db.session.add(category)
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
            updated_category = check_if_category_exists_and_return_or_false(current_user, form.category.data)
            if not updated_category:
                new_category = create_new_category(current_user, form.category.data)
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
    form = CreateCategoryForm()
    categories = db.session.scalars(sa.select(Category).where(current_user == Category.user))
    if form.validate_on_submit():
        new_category = create_new_category(current_user, form.name.data)
        db.session.add(new_category)
        db.session.commit()
        flash('New Category created!')
        return redirect(url_for('user_categories', username=current_user.username))
    return render_template('create_category.html', title='Create Category', form=form, categories=categories)

@app.route('/edit_category/<id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    #app.logger.info(f'Starting the edit_category route for category id: {id}')
    delete_afterwards = request.args.get('delete_afterwards', 'False') == 'True'
    #app.logger.info(f'delete_afterwards: {delete_afterwards}')
    current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
    form = EditCategoryForm()
    form.new_category.choices = [category.name for category in current_user.categories if category != current_category]

    if form.validate_on_submit():
        name_change = True if form.name.data != current_category.name else False
        reassign_gidguds = True if form.new_category.data != current_category.name else False
        gidguds_to_reassign = [gidgud.id for gidgud in current_category.gidguds] if reassign_gidguds else False

        #app.logger.info(f'current_category: {current_category}')
        #app.logger.info(f'name_change: {name_change}, reassign_gidguds: {reassign_gidguds},delete afterwards: {delete_afterwards}')

        if name_change:
            app.logger.info(f'This shows up if we reach the name change statement. name_change: {name_change}')
            if form.name.data in current_user.categories:
                flash('Category already exists. Please choose another name.')
            else:
                current_category.name = form.name.data
                db.session.commit()
                flash(f'Category {current_category.name} was renamed to {form.name.data}.')

        if reassign_gidguds:
            #app.logger.info(f'This shows up if we reach the reassign gidguds statement. reassign_gidguds: {reassign_gidguds}')
            new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
            for gidgud_id in gidguds_to_reassign:
                gidgud = db.session.query(GidGud).get(gidgud_id)
                gidgud.category = new_category
            db.session.commit()
            flash(f'The GidGuds from {current_category.name} were assigned to {new_category.name}')

        if delete_afterwards:
            #app.logger.info(f'This shows up if we reach the delete afterwards statement. delete afterwards: {delete_afterwards}')
            return redirect(url_for(f'delete_category', username=current_user.username, id=id))
        return redirect(url_for('user_categories', username=current_user.username))

    elif request.method == 'GET':
        form.name.data = current_category.name
        form.new_category.choices = [category.name for category in current_user.categories if category != current_category]
    return render_template('edit_category.html', title='Edit Category', form=form)

@app.route('/delete_category/<id>', methods=['GET', 'DELETE', 'POST'])
@login_required
def delete_category(id):
    current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
    if current_category.name == 'default':
        flash('The default Category may not be deleted')
        return redirect(url_for('user_categories', username=current_user.username))
    else:
        if not current_category.gidguds:
            db.session.delete(current_category)
            db.session.commit()
            flash('Category deleted!')
        else:
            flash('This Category has attached GidGuds. Please assign a new Category')
            delete_afterwards = True
            return redirect(url_for('edit_category', id=id, delete_afterwards=delete_afterwards))
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