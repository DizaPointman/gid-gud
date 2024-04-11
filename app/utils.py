# utils.py

from flask import flash, current_app
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

def check_and_return_list_of_possible_parents(current_category) -> list[str]:
    """
    Return a list of potential parent categories for the given current_category,
    adhering to a maximum of 3 category levels.

    Args:
        current_category (Category): The current category for which potential parents are to be determined.

    Returns:
        list[str]: A list of potential parent category names, including 'No Parent' option, or an empty list if no suitable parents are found.

    Raises:
        Exception: Any exception that occurs during the process is logged and an empty list is returned.

    Notes:
        - Case A: Categories with no children allow parents that have no parent (i.e., no grandparent).
        - Case B: Categories with children (but children have no children themselves) allow parents with no parent.
        - Case C: Categories with children that have children do not allow parents.

    """
    try:
        possible_parents = []

        # Case A: Category has no children
        if not current_category.children:
            possible_parents = [category.name for category in current_user.categories if (category.parent is None or category.parent.parent is None) and category.name != 'default']

        # Case B: Category has children, and the children do not have children
        elif current_category.children and not any(category.children for category in current_category.children):
            possible_parents = [category.name for category in current_user.categories if category.parent is None and category.name != 'default']

        # Case C: Category has children with children
        else:
            # No suitable parents for categories with grandchildren
            pass

        return possible_parents

    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return []

def check_and_return_list_of_possible_parents_for_children(current_category) -> list[str]:
    """
    Check and return the list of potential parent categories for the children of the given category.

    Args:
        current_category (Category): The category whose children are to be considered.

    Returns:
        list[str]: A list of potential parent categories for the children.
    """
    try:
        possible_parents = []
        remove_parent = ['No Parent']

        # Ensure eager loading of children to avoid N+1 query issue
        current_category = Category.query.filter_by(id=current_category.id).options(selectinload(Category.children)).first()

        # Check if any child category has children
        if current_category.children:
            # Check if any child category has its own children
            first_child_with_grandchildren = next((category for category in current_category.children if category.children), None)

            if first_child_with_grandchildren:
                # If a child category has grandchildren, determine potential parent categories recursively
                possible_parents = check_and_return_list_of_possible_parents(first_child_with_grandchildren)
            else:
                # If no child category has grandchildren, determine potential parent categories for any child
                possible_parents = check_and_return_list_of_possible_parents(current_category.children[0])

            possible_parents = remove_parent + possible_parents

        return possible_parents

    except Exception as e:
        # Log the exception with details
        log_exception(f"An error occurred while checking possible parent categories for children: {str(e)}")
        return []

# Category - create_object

def create_new_category(name: str, user_id: int) -> Category:
    """
    Create a new category with the given name and user ID.

    Args:
        name (str): The name of the new category.
        user_id (int): The ID of the user who owns the category.

    Returns:
        Category: The newly created category object.
    """
    new_category = Category(name=name, user_id=user_id)
    db.session.add(new_category)
    db.session.commit()
    return new_category

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
        if current_category.name == 'default':
            flash('The default category may not be renamed.')
        elif form.name.data in current_user.categories:
            flash('Category already exists. Please choose another name.')
        else:
            current_category.name = form.name.data
            flash(f'Category {current_category.name} was renamed to {form.name.data}.')
            db.session.commit()
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


def category_child_protection_service(current_category, form):
    """
    Reassign children from the current category to a new parent category or remove them from their parent based on user input.

    This function reassigns all categories belonging to the current category to a new parent category specified by the user through a form input. 
    If the specified new category is 'None', the categories are removed from their parent.

    Args:
        current_category: The current category whose children will be reassigned or removed.
        form: The Flask-WTF form object containing user input, including the name of the new parent category.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    try:
        # Extract the name of the new parent category from the form input
        new_name = form.reassign_children.data

        # Find the new parent category based on the provided name or set it to None if 'None' is specified
        if new_name == 'No Parent':
            new_parent_category_id = None
        else:
            new_parent_category_id = next((c.id for c in current_user.categories if c.name == new_name), None)

        # Update the parent_id of categories belonging to the current category using a query update
        db.session.query(Category).filter(Category.parent_id == current_category.id).update(
            {Category.parent_id: new_parent_category_id}, synchronize_session=False)

        # Commit the database transaction
        db.session.commit()

        # Provide feedback to the user about the successful reassignment or removal
        if new_parent_category_id:
            flash(f"Children reassigned to {new_name}")
        else:
            flash("Children removed from parent.")

        return True
    except Exception as e:
        # Log any exceptions that occur during the operation
        log_exception(e)
        return False


def category_handle_reassign_gidguds(current_category, form):
    """
    Reassign gidguds from the current category to a new category based on user input.

    This function reassigns all gidguds belonging to the current category to a new category specified by the user through a form input. 
    If the specified new category does not exist, the gidguds are reassigned to a default category.

    Args:
        current_category: The current category from which gidguds will be reassigned.
        form: The Flask-WTF form object containing user input, including the name of the new category.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    try:
        # Extract the name of the new category from the form input
        new_name = form.reassign_gidguds.data

        # Find the new category based on the provided name or default to a predefined default category
        new_category = next((c for c in current_user.categories if c.name == new_name), Category.query.filter_by(name='default').first())

        if new_category:
            # Update the category_id of gidguds belonging to the current category to the id of the new category
            db.session.query(GidGud).filter(GidGud.category_id == current_category.id).update(
                {GidGud.category_id: new_category.id}, synchronize_session=False)

            # Commit the database transaction
            db.session.commit()

            # Provide feedback to the user about the successful reassignment
            flash(f"GidGuds reassigned to {new_category.name}")
            return True
        else:
            # Flash a message indicating that the specified parent category was not found
            flash(f"Parent category '{new_name}' not found.")
            return False
    except Exception as e:
        # Log any exceptions that occur during the operation
        log_exception(e)
        return False
