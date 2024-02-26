from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateToDoForm, EditTodoForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, ToDo
from urllib.parse import urlsplit
from datetime import datetime, timezone

@app.route('/')
@app.route('/index')
@login_required
def index():
    todos = db.session.scalars(sa.select(ToDo).where(current_user == ToDo.author))
    return render_template('index.html', title='Home', todos=todos)

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

@app.route('/create_todo', methods=['GET', 'POST'])
@login_required
def create_todo():
    form = CreateToDoForm()
    todos = db.session.scalars(sa.select(ToDo).where(current_user == ToDo.author))
    if form.validate_on_submit():
        todo = ToDo(body=form.body.data, user_id=current_user.id, recurrence=form.recurrence.data, recurrence_rhythm=form.recurrence_rhythm.data)
        db.session.add(todo)
        db.session.commit()
        flash('New ToDo created!')
        return redirect(url_for('index'))
    return render_template('create_todo.html', title='Create ToDo', form=form, todos=todos)

@app.route('/edit_todo/<id>', methods=['GET', 'POST'])
@login_required
def edit_todo(id):
    todo = db.session.scalar(sa.select(ToDo).where(id == ToDo.id))
    form = EditTodoForm()
    if form.validate_on_submit():
        todo.body = form.body.data
        todo.recurrence = form.recurrence.data
        todo.recurrence_rhythm = form.recurrence_rhythm.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.body.data = todo.body
        form.recurrence.data = todo.recurrence
        form.recurrence_rhythm.data = todo.recurrence_rhythm
    return render_template('edit_todo.html', title='Edit ToDo', form=form)

@app.route('/delete_todo/<id>', methods=['GET', 'DELETE', 'POST'])
@login_required
def delete_todo(id):
    current_todo = db.session.scalar(sa.select(ToDo).where(id == ToDo.id))
    db.session.delete(current_todo)
    db.session.commit()
    flash('ToDo deleted!')
    return redirect(url_for('index'))

@app.route('/complete_todo/<id>', methods=['GET', 'POST'])
@login_required
def complete_todo(id):
    current_todo = db.session.scalar(sa.select(ToDo).where(id == ToDo.id))
    current_todo.completed = True
    db.session.commit()
    flash('ToDo completed!')
    return redirect(url_for('index'))

@app.route('/user/<username>/statistics', methods=['GET'])
@login_required
def statistics(username):
    todos = db.session.scalars(sa.select(ToDo).where(current_user == ToDo.author))
    return render_template('statistics.html', title='My Statistic', todos=todos)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    todos = db.session.scalars(sa.select(ToDo).where(current_user == ToDo.author))
    return render_template('user.html', user=user, todos=todos)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()