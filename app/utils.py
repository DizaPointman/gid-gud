# utils.py

from datetime import datetime, timedelta, timezone
import traceback
from typing import Optional
from flask import flash, current_app, request
from flask_login import current_user
from app.models import User, GidGud, Category
from app.factory import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DatabaseError
from sqlalchemy.orm import selectinload
import logging
import sqlalchemy as sa
from pytz import utc

# Define a function to generate ISO 8601 formatted strings
def iso_now():
    return datetime.now(utc).isoformat()

# Utility Functions

# General
# exception logger, debug helper, flash handler

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
        traceback.print_exc()

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

def log_form_validation_errors(form):
    for field in form:
        if field.errors:
            field_name = field.label.text
            errors = ", ".join(field.errors)
            current_app.logger.error(f"Validation failed for field '{field_name}': {errors}")

# debug helper

def log_request():
    request_data = request.form.to_dict()
    current_app.logger.info("Starting Request Logging")
    [current_app.logger.info(f"field: {k}, field data: {v}, field data type: {type(v)}") for k, v in request_data.items()]

def log_object(obj):
    attributes_to_log = ["id", "username", "body", "name", "category", "author", "user", "parent", "children", "gidguds"]
    current_app.logger.info(f"Starting Logging Object of type: {type(obj)}")
    for attribute in attributes_to_log:
        value = getattr(obj, attribute, None)
        if value is not None:
            current_app.logger.info(f"Attribute: {attribute}, Value: {value}, Type: {type(value)}")

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

def gidgud_return_dict_from_choice2(choice: list) -> dict:

    def check_sleep(gidgud):
        datetime_now = datetime.now(utc)
        gidgud_next_occurrence = datetime.fromisoformat(gidgud.next_occurrence)
        sleep = (gidgud_next_occurrence - datetime_now).total_seconds()
        return sleep

    choices = ['gids', 'guds', 'sleep', 'all']
    gidgud_dict = {}

    try:

        if 'all' in choice:
            gidguds = db.session.scalars(sa.select(GidGud).where(current_user == GidGud.author))
            gidgud_dict['all'] = gidguds

        if 'guds' in choice:
            guds = db.session.scalars(
                sa.select(GidGud)
                .where(current_user == GidGud.author)
                .filter(GidGud.completed == True)
            )
            gidgud_dict['guds'] = guds

        if 'gids' in choice or 'sleep' in choice:
            gids_and_sleep = db.session.scalars(
                sa.select(GidGud)
                .where(current_user == GidGud.author)
                .filter(GidGud.completed == False)
            )
            if 'gids' in choice:
                gids = [g for g in gids_and_sleep if not g.next_occurrence or (check_sleep(g) <= 0)]
                gidgud_dict['gids'] = gids
            if 'sleep' in choice:
                sleep = [g for g in gids_and_sleep if not g.next_occurrence or (check_sleep(g) > 0)]
                gidgud_dict['sleep'] = sleep

        return gidgud_dict

    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return False

def gidgud_return_dict_from_choice(choice: list) -> dict:

    def check_sleep(gidgud):
        datetime_now = datetime.now(utc)
        gidgud_next_occurrence = datetime.fromisoformat(gidgud.next_occurrence)
        sleep = (gidgud_next_occurrence - datetime_now).total_seconds()
        return sleep

    choices = ['gids', 'guds', 'sleep', 'all']
    gidgud_dict = {}

    try:
        if 'all' in choice:
            gidguds = db.session.execute(sa.select(GidGud).where(current_user == GidGud.author)).scalars().all()
            gidgud_dict['all'] = gidguds

        if 'guds' in choice:
            guds = db.session.execute(
                sa.select(GidGud)
                .where((current_user == GidGud.author) & (GidGud.completed.isnot(None)))
            ).scalars().all()
            gidgud_dict['guds'] = guds

        if 'gids' in choice or 'sleep' in choice:
            gids_and_sleep = db.session.scalars(
                sa.select(GidGud)
                .where((current_user == GidGud.author) & (GidGud.completed.is_(None)))
            )
            gids = []
            sleep = []

            for gidgud in gids_and_sleep:
                if 'gids' in choice:
                    if not gidgud.next_occurrence or (check_sleep(gidgud) <= 0):
                        gids.append(gidgud)
                if 'sleep' in choice:
                    if gidgud.next_occurrence and check_sleep(gidgud) > 0:
                        sleep.append(gidgud)

            if 'gids' in choice:
                gidgud_dict['gids'] = gids
            if 'sleep' in choice:
                gidgud_dict['sleep'] = sleep

        return gidgud_dict

    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return False



# GidGud - create_object
# GidGud - handle_and_update_object

def gidgud_handle_update(gidgud, form, c_man):

    try:
        gidgud.body = form.body.data
        if form.category.data is not gidgud.category.name:
            updated_category = c_man.return_or_create_category(name=(form.category.data))
            gidgud.category = updated_category
        if form.rec_rhythm.data is not gidgud.recurrence_rhythm:
            gidgud.recurrence_rhythm = form.rec_rhythm.data
            if gidgud.next_occurrence is not None:
                gidgud.next_occurrence = None
        if form.time_unit.data is not gidgud.time_unit:
            gidgud.time_unit = form.time_unit.data
            if gidgud.next_occurrence is not None:
                gidgud.next_occurrence = None
        db.session.commit()
        return True

    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return False

def gidgud_handle_complete(current_gidgud):
    try:
        timestamp = datetime.now(utc).isoformat()
        if current_gidgud.recurrence_rhythm == 0:
            current_gidgud.completed = timestamp
            db.session.commit()
            return True
        else:
            gud = GidGud(body=current_gidgud.body, user_id=current_gidgud.user_id, category=current_gidgud.category, completed=timestamp)

            if current_gidgud.recurrence_rhythm == 1 and current_gidgud.time_unit == 'None':
                next_occurrence = iso_now()
            else:
                delta = timedelta(**{current_gidgud.time_unit: current_gidgud.recurrence_rhythm})
                next_occurrence = (datetime.fromisoformat(timestamp) + delta).isoformat()

            current_gidgud.next_occurrence = next_occurrence
            db.session.add(gud)
            db.session.commit()
            return True
    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return False