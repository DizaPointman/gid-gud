# utils.py

from flask import flash
from flask_login import current_user
from app.models import User, GidGud, Category
from app import db
import sqlalchemy as sa

# Category management

def check_if_category_exists_and_return_or_false(user, category_name):
    category_name = category_name or 'default'
    for category in user.categories:
        if category_name == category.name:
            return category
    return False

def create_new_category(user, category_name):
    return Category(name=category_name, user_id=user.id)

def check_if_category_has_gidguds_and_return_list(category):
    if category.gidguds is None:
        return False
    else:
        return category.gidguds

def update_gidgud_category(gidgud, new_category):
    gidgud.category = new_category

def handle_name_change(current_category, form):
    name_change = form.name.data != current_category.name
    if name_change:
        if form.name.data in current_user.categories:
            flash('Category already exists. Please choose another name.')
        else:
            current_category.name = form.name.data
            db.session.commit()
            flash(f'Category {current_category.name} was renamed to {form.name.data}.')

def handle_reassign_gidguds(current_category, form):
    reassign_gidguds = form.new_category.data != current_category.name
    if reassign_gidguds:
        new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
        gidguds_to_reassign = [gidgud.id for gidgud in current_category.gidguds]
        for gidgud_id in gidguds_to_reassign:
            gidgud = db.session.query(GidGud).get(gidgud_id)
            gidgud.category = new_category
        db.session.commit()
        flash(f'The GidGuds from {current_category.name} were assigned to {new_category.name}')

def delete_category(user, category_name):
    return True

def add_parent_category(user, category_name, parent_category_name):
    return True

def remove_parent_category(user, category_name, parent_category_name):
    return True

def add_children_to_category(user, category_name, child_category_name):
    return True