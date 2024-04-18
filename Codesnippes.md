/* cSpell:disable */

# Create default category on registration

    from sqlalchemy import event

    # Define your User and Category models here

    # Define event listener function to create default category for new users
    def create_default_category_for_user(mapper, connection, target):
        from your_module import db, Category  # Import the necessary modules

        # Create a default category for the new user
        default_category = Category(name='default', user=target)
        db.session.add(default_category)
        db.session.commit()

    # Attach the event listener to the User model
    event.listen(User, 'after_insert', create_default_category_for_user)

    # Informative message to Sensei
    print("A default category will be created for each new user.")

# Template

# Logging

# Validators

    def optional_choice(form, field):
        current_app.logger.info("starting optional choice validator")
        current_app.logger.info(f"evaluating: {field}, data: {field.data}, type: {type(field.data)}")
        current_app.logger.info(f"field data - if field.data is None or 'None': {field.data in (None, 'None')}")
        if field.data in (None, 'None'):
            current_app.logger.info("field data - check")
        #if not field.data:
            current_app.logger.info(f"not field data: {field.data}")
            field.data = field.choices[0]
            current_app.logger.info(f"field choices [0]: {field.choices[0]}")
            current_app.logger.info(f"new field data: {field.data}")
            current_app.logger.info(f"before form validation: name: {request.form.get('name')}, parent: {request.form.get('parent')}, parent type: {type(request.form.get('parent'))}, gidgud: {request.form.get('reassign_gidguds')}, children: {request.form.get('reassign_children')}, childrentype: {type(request.form.get('reassign_children'))}")
            return True
        current_app.logger.info(f"field data + , data: {field.data}")
        choices = field.choices
        current_app.logger.info(f"choices: {choices}")
        if field.data in choices:
            current_app.logger.info(f"field data in choices: {field.data in choices}")
            current_app.logger.info(f"before form validation: name: {request.form.get('name')}, parent: {request.form.get('parent')}, parent type: {type(request.form.get('parent'))}, gidgud: {request.form.get('reassign_gidguds')}, children: {request.form.get('reassign_children')}, childrentype: {type(request.form.get('reassign_children'))}")
            return True
        else:
            raise ValidationError('Invalid choice')

# Routes


## SQL to log file

    import logging
    from logging.handlers import RotatingFileHandler
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy

    # Initialize Flask application
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('sqlalchemy.engine')
    file_handler = RotatingFileHandler('sql.log', maxBytes=1024 * 1024, backupCount=10)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Initialize SQLAlchemy extension
    db = SQLAlchemy(app)

    # Import routes and other modules
    from . import routes  # Import your routes module

## Log to terminal

    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    import logging

    # Initialize Flask application
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Set up logging
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').addHandler(logging.StreamHandler())

    # Initialize SQLAlchemy extension
    db = SQLAlchemy(app)

    # Import routes and other modules
    from . import routes  # Import your routes module

# Utility

    def category_handle_reassign_children(current_category, form):
    """
    Reassigns the parent category for all children categories of the current category.

    Args:
        current_category: The current category whose children are to be reassigned.
        form: The form containing the new parent category data.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    try:
        # Find the new parent category
        new_parent = next((category for category in current_user.categories if category.name == form.parent.data), None)

        # Reassign the parent category for each child category
        for child_category in itertools.islice(current_category.children, len(current_category.children)):
            child_category.parent = new_parent

        # Flash message indicating successful parent change
        flash(f"Parent of children changed to {new_parent.name or 'None'}")
        return True
    except Exception as e:
        # Log any exceptions that occur
        log_exception(e)
        return False

    def check_category_level(current_category) -> dict:
    """
    Check if adding a parent or children to the current category is allowed based on the maximum category level constraint.

    Args:
        current_category (Category): The category to check.

    Returns:
        dict: A dictionary indicating whether adding a parent or children is allowed.
            - 'parent_allowed': True if adding a parent is allowed, False otherwise.
            - 'child_allowed': True if adding children is allowed, False otherwise.
    """
    level: dict[str, bool] = {'parent_allowed': True, 'child_allowed': True}
    try:
        # Check if adding children is allowed
        if current_category.parent and current_category.parent.parent:
            level['child_allowed'] = False

        # Check if adding a parent is allowed
        has_grandchildren = any(category.children for category in current_category.children)
        if has_grandchildren:
            level['parent_allowed'] = False

        return level
    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return False

def get_potential_parent_categories(current_category):
    """
    Get a list of potential parent categories for the given current category.

    Args:
        current_category (Category): The current category.

    Returns:
        list: A list of potential parent categories.
    """
    try:
        potential_parents = []

        # Case a: Current category has no children
        if not current_category.children:
            # Add categories that are two levels above
            potential_parents = Category.query.filter(Category.id != current_category.id) \
                                               .filter(Category.parent_id != current_category.id) \
                                               .all()

        # Case b: Current category has children, but the children have no children themselves
        elif not any(child.children for child in current_category.children):
            # Add categories that are one level above
            potential_parents = Category.query.filter(Category.id != current_category.id) \
                                               .filter(Category.parent_id != current_category.id) \
                                               .all()

        # Case c: The current category has children and these also have children
        else:
            # No parent is allowed in this case, return an empty list
            pass

        return potential_parents
    except Exception as e:
        # Log any exceptions that occur during the process
        log_exception(e)
        return []