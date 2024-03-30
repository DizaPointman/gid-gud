# utils.py

from app.models import User, GidGud, Category

def check_if_category_exists(user, category_name):
    for category in user.categories:
        if category_name == category.name: return category
    return False

def create_new_category(user, category_name):
    return Category(name=category_name, user_id=user.id)