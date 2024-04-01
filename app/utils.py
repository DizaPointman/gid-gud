# utils.py

from app.models import User, GidGud, Category

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

def delete_category(user, category_name):
    return True

def add_parent_category(user, category_name, parent_category_name):
    return True

def remove_parent_category(user, category_name, parent_category_name):
    return True

def add_children_to_category(user, category_name, child_category_name):
    return True