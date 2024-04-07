# utils.py

from flask import flash
from flask_login import current_user
from app.models import User, GidGud, Category
from app import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DatabaseError
from sqlalchemy.orm import selectinload
import logging
import sqlalchemy as sa
import itertools

# Utility Functions

# General
# exception logger, flash handler

# Models
# user, gidgud, category

# check_and_return_or_false / function will return object, list of objects or false
# create_object / function will create and return the new object or False
# handle_and_update_object / function will update or modify object and related objects and return True if successful or False otherwise

# exception logger

def log_exception(exception: Exception) -> None:
    """
    Log exception details.

    Parameters:
        exception (Exception): The exception that occurred.
    """
    error_msg = f"An error occurred: {exception}"
    if isinstance(exception, SQLAlchemyError):
        logging.error(f"An SQLAlchemy error occurred: {exception}")
    elif isinstance(exception, IntegrityError):
        logging.error(f"An Integrity error occurred: {exception}")
    elif isinstance(exception, DatabaseError):
        logging.error(f"A database error occurred: {exception}")
    elif isinstance(exception, OperationalError):
        logging.error(f"An Operational error occurred: {exception}")
    elif isinstance(exception, ProgrammingError):
        logging.error(f"A Programming error occurred: {exception}")
    else:
        logging.error(error_msg)

# flash handler
def flash_successful_change(name, current, new):
    message = f"{name} of {current} was changed to {new}"
    return message

def flash_successful_reassign(collection, current, new):
    message = f"{collection} of {current} was reassigned to {new}"
    return message

def flash_warning_existing(name):
    message = f"{name} already exists. Please choose a different name."
    return message

def flash_warning_not_empty(name, collection):
    message = f"{name} has {collection}. Please reassign."
    return message

# User

# User - check_and_return

def check_alerts():
# TODO: Implement alert
# FIXME: This function is not optimized
# BUG: to be implemented
    return True if current_user.alerts else False

def check_and_return_all_gidguds() -> list:
    """
    Check if gidguds exist for the current user and return them.

    Returns:
        list: A list of gidguds associated with the current user, or False if none exist.
    """
    try:
        gidguds = current_user.gidguds
        return gidguds if gidguds else False
    except Exception as e:
        log_exception(e)
        return False

def check_and_return_all_categories() -> list:
    """
    Check if categories exist for the current user and return them.

    Returns:
        list: A list of categories associated with the current user, or False if none exist.
    """
    try:
        categories = current_user.categories
        return categories if categories else False
    except Exception as e:
        log_exception(e)
        return False

# User - create_object
# User - handle_and_update_object

# GidGud
# GidGud - check_and_return
# GidGud - create_object
# GidGud - handle_and_update_object

# Category
# Category - check_and_return

def check_if_category_exists_and_return(new_cat_name):
    """
    Check if a category with the given name exists for the current user.

    Args:
        new_cat_name (str): The name of the category to check.

    Returns:
        Category or bool: The category object if it exists, otherwise False.
    """
    try:
        new_cat_name = new_cat_name or 'default'
        category = next((category for category in current_user.categories if category.name == new_cat_name), None)
        if category:
            return category
        else:
            return False
    except Exception as e:
        log_exception(e)
        return False

# Category - create_object
# Category - handle_and_update_object

def category_handle_rename(current_category, form):
    try:
        if form.name.data in current_user.categories:
            flash('Category already exists. Please choose another name.')
        else:
            current_category.name = form.name.data
            db.session.commit()
            flash(f'Category {current_category.name} was renamed to {form.name.data}.')
    except Exception as e:
        log_exception(e)
        return False

def category_handle_reassign_children(current_category, form):
    try:
        # Retrieve new parent category
        new_parent_name = form.parent.data
        new_parent = next((category for category in current_user.categories if category.name == new_parent_name), None)

        if new_parent:
            # Use selectinload to eagerly load children of current_category
            db.session.query(Category).filter_by(id=current_category.id).options(selectinload(Category.children)).first()

            # Update parent for each child category
            for child_category in current_category.children:
                child_category.parent = new_parent

            # Commit changes
            db.session.commit()

            # Flash message
            flash(f"Parent of children changed to {new_parent_name}")
        else:
            flash(f"Parent category '{new_parent_name}' not found.")
    except Exception as e:
        log_exception(e)
        return False
