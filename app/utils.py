# utils.py

from flask import flash
from flask_login import current_user
from app.models import User, GidGud, Category
from app import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DatabaseError
from sqlalchemy.orm import selectinload
import logging
import sqlalchemy as sa

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
    try:
        # Initialize the error message with a generic message
        error_msg = f"An error occurred: {exception}"

        # Check the type of exception and log accordingly
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
            # If the exception type is not recognized, log the generic error message
            logging.error(error_msg)
    except Exception as e:
        # If an error occurs while logging the exception, log it as well
        logging.error(f"Error logging exception: {e}")

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
        # Retrieve all gidguds associated with the current user
        gidguds = current_user.gidguds

        # Return the list of gidguds if it exists, otherwise return False
        return gidguds if gidguds else False
    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return False


def check_and_return_all_categories() -> list:
    """
    Check if categories exist for the current user and return them.

    Returns:
        list: A list of categories associated with the current user, or False if none exist.
    """
    try:
        # Retrieve all categories associated with the current user
        categories = current_user.categories

        # Return the list of categories if it exists, otherwise return False
        return categories if categories else False
    except Exception as e:
        # Log any exceptions that occur during the process
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
    Check if a category with the given name exists for the current user and return the category object.

    Args:
        new_cat_name (str): The name of the category to check.

    Returns:
        Category or bool: The category object if it exists, otherwise False.
    """
    try:
        # Ensure a default category name if None is provided
        new_cat_name = new_cat_name or 'default'

        # Search for the category with the given name among the current user's categories
        category = next((category for category in current_user.categories if category.name == new_cat_name), None)

        # Return the category object if found, otherwise return False
        if category:
            return category
        else:
            return False
    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return False


# Category - create_object
# Category - handle_and_update_object

def category_handle_rename(current_category, form):
    """
    Rename the current category based on user input.

    Args:
        current_category: The current category to be renamed.
        form: The form containing user input, including the new category name.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    try:
        if form.name.data in current_user.categories:
            flash('Category already exists. Please choose another name.')
        else:
            current_category.name = form.name.data
            db.session.commit()
            flash(f'Category {current_category.name} was renamed to {form.name.data}.')
            return True
    except Exception as e:
        # Log any exceptions
        log_exception(e)
        return False


def category_handle_change_parent(current_category, form):
    """
    Change the parent category of the current category based on user input.

    Args:
        current_category: The current category whose parent will be changed.
        form: The form containing user input, including the new parent category.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """

    try:
        # Retrieve new parent category
        new_parent_name = form.parent.data
        new_parent = next((category for category in current_user.categories if category.name == new_parent_name), None)

        # Update parent
        current_category.parent = new_parent

        # Flash message
        if new_parent is None:
            flash(f"Parent removed from category {current_category.name}.")
        else:
            flash(f"{new_parent.name} added as parent to category {current_category.name}.")

        # Commit changes
        db.session.commit()
        return True
    except Exception as e:
        # Log any exceptions
        log_exception(e)
        return False


def category_handle_reassign_children(current_category, form):
    """
    Reassign children categories of the current category to a new parent category based on user input.

    Args:
        current_category: The current category whose children will be reassigned.
        form: The form containing user input, including the new parent category.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """

    try:
        # Retrieve new parent category for children
        new_parent_name = form.parent.data
        new_parent = next((category for category in current_user.categories if category.name == new_parent_name), None)

        if new_parent:
            # Use selectinload to eagerly load children of current_category
            db.session.query(Category).filter_by(id=current_category.id).options(selectinload(Category.children)).first()

            # Update parent for each child category
            for child_category in current_category.children:
                child_category.parent = new_parent

            # Flash message
            flash(f"Parent of children changed to {new_parent_name}")
            # Commit changes
            db.session.commit()
            return True
        else:
            flash(f"Parent category '{new_parent_name}' not found.")
            return False
    except Exception as e:
        # Log any exceptions
        log_exception(e)
        return False


def category_handle_reassign_gidguds(current_category, form):
    """
    Reassign gidguds from the current category to a new category based on user input.

    Args:
        current_category: The current category from which gidguds will be reassigned.
        form: The form containing user input, including the new category.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """

    # Set default category as default for gidguds to be reassigned
    default_category = Category.query.filter(Category.name == 'default').first()

    try:
        # Retrieve new category for gidguds
        new_category_for_gidguds = form.new_category.data
        new_category_for_gidguds = next((category for category in current_user.categories if category.name == new_category_for_gidguds), default_category)

        if new_category_for_gidguds:
            # Use selectinload to eagerly load gidguds of current_category
            db.session.query(Category).filter_by(id=current_category.id).options(selectinload(Category.gidguds)).first()

            # Update category for each gidgud of current_category
            for gidgud in current_category.gidguds:
                gidgud.category = new_category_for_gidguds

            # Flash message
            flash(f"GidGuds reassigned to {new_category_for_gidguds.name}")
            # Commit changes
            db.session.commit()
            return True
        else:
            flash(f"Parent category '{new_category_for_gidguds}' not found.")
            return False
    except Exception as e:
        # Log any exceptions
        log_exception(e)
        return False

