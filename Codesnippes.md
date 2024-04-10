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

# Routes

    @app.route('/delete_and_reassign_category/<id>', methods=['GET', 'DELETE', 'POST'])
    @login_required
    def delete_and_reassign_category(id):
        current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
        cat_name = current_category.name
        form = AssignNewCategoryOnDelete()
        form.new_category.choices = [category.name for category in current_user.categories if category != current_category]
        if form.validate_on_submit():
            attached_gidguds = check_if_category_has_gidguds_and_return_list(current_category)
            for gidgud in attached_gidguds:
                app.logger.info(f"ID: {gidgud.id}, BODY:{gidgud}, Category ID: {gidgud.category.id} Category GidGuds: {gidgud.category.gidguds}")
            new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
            app.logger.info(f"Current Cat ID: {current_category.id}, Current Cat Name: {current_category}, GidGuds: {current_category.gidguds}")
            app.logger.info(f"New Cat ID: {new_category.id}, New Cat Name: {new_category}, GidGuds: {new_category.gidguds}")
            for gidgud in attached_gidguds:
                gidgud.category = new_category
                app.logger.info(f"GidGud ID: {gidgud.id}, Category: {gidgud.category}, GidGuds: {gidgud.category.gidguds}")
                #update_gidgud_category(gidgud, new_category)
            db.session.commit()
            db.session.delete(current_category)
            db.session.commit()
            flash(f'Category: {cat_name} deleted!')
            return redirect(url_for('user_categories', username=current_user.username))
        return render_template('delete_and_reassign_category.html', title='Assign new Category', form=form, id=id)



    @app.route('/edit_category/<id>', methods=['GET', 'DELETE', 'POST'])
    @login_required
    def edit_category(id):
        current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
        form = EditCategoryForm()
        form.new_category.choices = [category.name for category in current_user.categories if category != current_category]
        if form.validate_on_submit():

            if form.name.data != current_category.name:
                if form.name.data in current_user.categories:
                    flash('Category already exists. Please choose another name.')
                else:
                    if form.new_category.data == current_category.name and current_category.name != form.name.data:
                        current_category.name = form.name.data
                        db.session.commit()
                        flash(f'Category {current_category.name} was renamed to {form.name.data}.')
                        return redirect(url_for('user_categories', username=current_user.username))
                    elif form.new_category.data == current_category.name and current_category.name == form.name.data:
                        flash('No changes were made.')
                        return redirect(url_for('user_categories', username=current_user.username))
                    elif form.new_category.data != current_category.name and current_category.name != form.name.data:
                        current_category.name = form.name.data
                        db.session.commit()
                        new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
                        for gidgud in new_category.gidguds:
                            update_gidgud_category(gidgud, new_category)
                            db.session.commit()
                        flash(f'Category {current_category.name} was renamed to {form.name.data}.')
                        flash(f'Attached GidGuds were assigned from Category {current_category.name} to Category {new_category.name}')
                        return redirect(url_for('user_categories', username=current_user.username))
                    elif form.new_category.data != current_category.name and current_category.name == form.name.data:
                        new_category = db.session.scalar(sa.select(Category).where(Category.name == form.new_category.data))
                        for gidgud in new_category.gidguds:
                            update_gidgud_category(gidgud, new_category)
                            db.session.commit()
                        flash(f'Attached GidGuds were assigned from Category {current_category.name} to Category {new_category.name}')
                        return redirect(url_for('user_categories', username=current_user.username))
        elif request.method == 'GET':
            form.name.data = current_category.name
            form.new_category.choices = [category.name for category in current_user.categories if category != current_category]
        return render_template('edit_category.html', title='Edit Category', form=form)

# Logging

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