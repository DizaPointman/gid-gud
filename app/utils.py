# utils.py

from datetime import datetime, timedelta, timezone
import inspect
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

def log_exception(exception: Exception, module_name: str, function_name: str) -> None:
    """
    Log exception details including the stack trace.

    Parameters:
        exception (Exception): The exception that occurred.
        module_name (str): The name of the module where the exception occurred.
        function_name (str): The name of the function where the exception occurred.
    """
    # Capture the stack trace
    stack_trace = traceback.format_exc()

    # Log the timestamp, module, and function names
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.error(f"Timestamp: {timestamp}, Module: {module_name}, Function: {function_name}")

    # Log the stack trace at the debug level
    logging.debug(stack_trace)

    # Initialize the error message with a generic message
    error_msg = f"An error occurred: {exception}"

    # Check the type of exception and log accordingly
    if isinstance(exception, IntegrityError):
        logging.error(f"An Integrity error occurred: {exception}")
    elif isinstance(exception, DatabaseError):
        logging.error(f"A database error occurred: {exception}")
    elif isinstance(exception, OperationalError):
        logging.error(f"An Operational error occurred: {exception}")
    elif isinstance(exception, ProgrammingError):
        logging.error(f"A Programming error occurred: {exception}")
    elif isinstance(exception, SQLAlchemyError):
        logging.error(f"An SQLAlchemy error occurred: {exception}")
    else:
        # If the exception type is not recognized, log the generic error message
        logging.error(error_msg)

    # Optionally log the stack trace at the error level
    logging.error(stack_trace)

def handle_exception(exception):
    """
    Handle exceptions by logging, rolling back the session, and re-raising the exception.

    Parameters:
        exception (Exception): The exception that occurred.
    """
    module_name = inspect.getmodule(inspect.stack()[1][0]).__name__
    function_name = inspect.currentframe().f_back.f_code.co_name
    log_exception(exception, module_name, function_name)
    db.session.rollback()
    raise exception

# debug helper

def log_request():
    request_data = request.form.to_dict()
    current_app.logger.info("Starting Request Logging")
    [current_app.logger.info(f"field: {k}, field data: {v}, field data type: {type(v)}") for k, v in request_data.items()]

def log_form_validation_errors(form):
    for field in form:
        if field.errors:
            field_name = field.label.text
            errors = ", ".join(field.errors)
            current_app.logger.error(f"Validation failed for field '{field_name}': {errors}")

def log_object(obj):
    attributes_to_log = ["id", "username", "body", "name", "category", "author", "user", "parent", "children", "gidguds"]
    current_app.logger.info(f"Starting Logging Object of type: {type(obj)}")
    for attribute in attributes_to_log:
        value = getattr(obj, attribute, None)
        if value is not None:
            current_app.logger.info(f"Attribute: {attribute}, Value: {value}, Type: {type(value)}")