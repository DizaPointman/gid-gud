/* cSpell:disable */

# Chat GPT

I need the functionality to check the the following:
a) a category may have a parent and children
b) the children of a category that already has a parent are not allowed to have children
c) a category with children where at least one child has children too, is not allowed to have a parent

please evaluate where it is suitable to implement this. options:
a) a class function for the category model
b) a custom validator in the Flaskform
c) a utility function

list advantages and disadvantages for the different approaches. suggest better approaches

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

# Routes

# Logging

# Routes

Former part of edit category route

        name_change = True if form.name.data != current_category.name else False
        change_parent = True if form.parent.data != default_parent_choices else False
        reassign_gidguds = True if form.new_category.data != current_category.name else False
        gidguds_to_reassign = [gidgud.id for gidgud in current_category.gidguds] if reassign_gidguds else False

        #app.logger.info(f'current_category: {current_category}')
        #app.logger.info(f'name_change: {name_change}, reassign_gidguds: {reassign_gidguds},delete afterwards: {delete_afterwards}')

        if name_change:
            app.logger.info(f'This shows up if we reach the name change statement. name_change: {name_change}')
            if form.name.data in current_user.categories:
                flash('Category already exists. Please choose another name.')
            else:
                current_category.name = form.name.data
                db.session.commit()
                flash(f'Category {current_category.name} was renamed to {form.name.data}.')

        if change_parent:
            if has_children:
                if form.parent.data == 'None':
                    for category in current_category.children:
                        category.parent = None
                    flash(f'The subcategories of <{current_category.name}> are now normal categories.')
                else:
                    new_parent = db.session.scalar(sa.select(Category).where(Category.name == form.parent.data))
                    for category in current_category.children:
                        category.parent = new_parent
                    flash(f'The subcategories of <{current_category.name}> are now a subcategories of <{new_parent.name}>.')
            else:
                if form.parent.data == 'None':
                    current_category.parent = None
                    flash(f'Category <{current_category.name}> is not a subcategory anymore.')
                else:
                    new_parent = db.session.scalar(sa.select(Category).where(Category.name == form.parent.data))
                    current_category.parent = new_parent
                    flash(f'Category <{current_category.name}> is now a subcategory of <{new_parent.name}>.')
            db.session.commit()

        if reassign_gidguds:
            #app.logger.info(f'This shows up if we reach the reassign gidguds statement. reassign_gidguds: {reassign_gidguds}')
            new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
            for gidgud_id in gidguds_to_reassign:
                gidgud = db.session.query(GidGud).get(gidgud_id)
                gidgud.category = new_category
            db.session.commit()
            flash(f'The GidGuds from {current_category.name} were assigned to {new_category.name}')

        if delete_afterwards:
            #app.logger.info(f'This shows up if we reach the delete afterwards statement. delete afterwards: {delete_afterwards}')
            return redirect(url_for(f'delete_category', username=current_user.username, id=id))
        return redirect(url_for('user_categories', username=current_user.username))

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