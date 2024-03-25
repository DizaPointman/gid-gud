from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateGidForm, EditGidForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, Gid
from urllib.parse import urlsplit
from datetime import datetime, timezone

@app.route('/')
@app.route('/index')
@login_required
def index():
    gids = db.session.scalars(sa.select(Gid).where(current_user == Gid.author))
    return render_template('index.html', title='Home', gids=gids)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
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

@app.route('/create_gid', methods=['GET', 'POST'])
@login_required
def create_gid():
    form = CreateGidForm()
    gids = db.session.scalars(sa.select(Gid).where(current_user == Gid.author))
    if form.validate_on_submit():
        number = current_user.categorize(form.category.data)
        gid = Gid(body=form.body.data, user_id=current_user.id, number=number, recurrence=form.recurrence.data, recurrence_rhythm=form.recurrence_rhythm.data, category=form.category.data)
        db.session.add(gid)
        db.session.commit()
        #flash('New Gid created!')
        return redirect(url_for('index'))
    return render_template('create_gid.html', title='Create Gid', form=form, gids=gids)

@app.route('/edit_gid/<id>', methods=['GET', 'POST'])
@login_required
def edit_gid(id):
    gid = db.session.scalar(sa.select(Gid).where(id == Gid.id))
    form = EditGidForm()
    if form.validate_on_submit():
        gid.body = form.body.data
        gid.recurrence = form.recurrence.data
        gid.recurrence_rhythm = form.recurrence_rhythm.data
        if gid.category is not form.category.data:
            current_user.update_category(gid.number, form.category.data)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.body.data = gid.body
        form.recurrence.data = gid.recurrence
        form.recurrence_rhythm.data = gid.recurrence_rhythm
        form.category.data = gid.category
    return render_template('edit_gid.html', title='Edit Gid', form=form)

@app.route('/delete_gid/<id>', methods=['GET', 'DELETE', 'POST'])
@login_required
def delete_gid(id):
    current_gid = db.session.scalar(sa.select(Gid).where(id == Gid.id))
    db.session.delete(current_gid)
    db.session.commit()
    flash('Gid deleted!')
    return redirect(url_for('index'))

@app.route('/complete_gid/<id>', methods=['GET', 'POST'])
@login_required
def complete_gid(id):
    current_gid = db.session.scalar(sa.select(Gid).where(id == Gid.id))
    current_gid.completed = True
    db.session.commit()
    flash('Gid completed!')
    return redirect(url_for('index'))

@app.route('/user/<username>/statistics', methods=['GET'])
@login_required
def statistics(username):
    gids = db.session.scalars(sa.select(Gid).where(current_user == Gid.author))
    return render_template('statistics.html', title='My Statistic', gids=gids)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    gids = db.session.scalars(sa.select(Gid).where(current_user == Gid.author))
    return render_template('user.html', user=user, gids=gids)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()