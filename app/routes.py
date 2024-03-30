from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateGidGudForm, EditGidGudForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, GidGud, Category
from urllib.parse import urlsplit
from datetime import datetime, timezone
#from app.utils import

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
        category_name = form.category.data or 'default'
        app.logger.info(f'category_name: {category_name}')
        category = current_user.check_if_category_exists(category_name)
        app.logger.info(f'category already exists: {category}')
        if not category:
            category = Category(name=category_name, user_id=current_user.id)
            db.session.add(category)
        gidgud = GidGud(body=form.body.data, user_id=current_user.id, recurrence=form.recurrence.data, recurrence_rhythm=form.recurrence_rhythm.data, category=category)
        db.session.add(gidgud)
        db.session.commit()
        #flash('New GidGud created!')
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
            updated_category = current_user.check_if_category_exists(form.category.data)
            if not updated_category:
                updated_category = Category(name=form.category.data, user_id=current_user.id)
                db.session.add(updated_category)
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