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

# Template


            <p>
                {{ form.reassign_children.label }} {{ form.reassign_children }}<br>
                {% for error in form.reassign_children.errors %}
                    <span style="color: red;">[{{ error }}]</span>
                {% endfor %}
            </p>

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

    # Construct a list of default parent choices, starting with the name of the current category's parent if it exists,
    # otherwise set it to 'No Parent'
    default_parent_choices = [current_category.parent.name] + ['No Parent'] if current_category.parent else ['No Parent']
    app.logger.info(f'default parent choices: {default_parent_choices}')

    # Retrieve a list of possible parent categories for the given current category if it's not the default category
    app.logger.info(f'before calling category check for parents')
    possible_parent_choices = [] if current_category.name == 'default' else category_check_and_return_possible_parents(current_category)
    app.logger.info(f'possible parents in route: {possible_parent_choices}')

    # Combine the default parent choices with the possible parent choices to form the final list of parent choices
    parent_choices = default_parent_choices + possible_parent_choices
    app.logger.info(f'final parent_choices: {parent_choices}')

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

    # current routes
@app.route('/edit_category/<id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    # TODO: update delete_afterwards interpreter
    # TODO: change choices to exclude the current category on deletion
    # TODO: add multiple children at once

    current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
    app.logger.info(f'Starting the edit_category route for category id: {id}, name: {current_category.name}')
    #delete_afterwards = request.args.get('delete_afterwards', 'False') == 'True'
    dla = request.args.get('dla') or {}
    delete_afterwards = bool(dla)
    #if not dla:
        #dla = {}
    app.logger.info(f'dla on start of edit route: {dla}')
    app.logger.info(f'delete_afterwards: {delete_afterwards}')

    app.logger.info(f'category to edit: {current_category.name}, id: {current_category.id}, parent: {current_category.parent}, children: {current_category.children}')


    # Choices: all categories except the current category
    gidgud_reassignment_choices = [current_category.name] + [category.name for category in current_user.categories if category != current_category]

    default_parent_choices = [current_category.parent.name] + ['No Parent'] if current_category.parent else ['No Parent']
    parent_choices = default_parent_choices + check_and_return_list_of_possible_parents(current_category)

    default_parent_choices_for_children = ['No Children']
    parent_choices_for_children = check_and_return_list_of_possible_parents_for_children(current_category) or default_parent_choices_for_children

    form = EditCategoryForm()
    # Assigning choices to selection fields
    form.parent.choices = parent_choices
    form.reassign_gidguds.choices = gidgud_reassignment_choices
    form.reassign_children.choices = parent_choices_for_children

    if form.validate_on_submit():


        # Check if form contains new parent
        if form.parent.data != ('No Parent' if current_category.parent is None else current_category.parent.name):
            app.logger.info(f'calling parent change: old:{current_category.parent}, new: {form.parent.data}')
            # Assign new parent
            category_handle_change_parent(current_category, form)

        # Check if form contains new category for gidguds
        if form.reassign_gidguds.data != current_category.name:
            app.logger.info(f'calling reassign gidguds: old:{current_category.name}, new: {form.reassign_gidguds.data}')
            # Assign gidguds to new category
            category_handle_reassign_gidguds(current_category, form)

        # Check if form contains a new parent category for the current category's children
        if form.reassign_children.data not in (default_parent_choices_for_children, current_category.name, 'No Children'):
            # Assign children categories to the new parent category
            category_child_protection_service(current_category, form)

        # Check if form contains new category name
        if form.name.data != current_category.name:
            app.logger.info(f'calling name change: old:{current_category.name}, new {form.name.data}')
            # Assign new category name
            category_handle_rename(current_category, form)

        #if delete_afterwards:
        if delete_afterwards:
            app.logger.info(f'This shows up if we reach the delete afterwards statement in edit: {dla}')
            return redirect(url_for('delete_category', username=current_user.username, id=id))
        return redirect(url_for('user_categories', username=current_user.username))

    elif request.method == 'GET':
        # populating fields for get requests
        form.name.data = current_category.name
        form.parent.choices = parent_choices
        form.reassign_gidguds.choices = gidgud_reassignment_choices
        form.reassign_children.choices = parent_choices_for_children

    return render_template('edit_category.html', title='Edit Category', id=id, form=form, dla=dla)

@app.route('/delete_category/<id>', methods=['GET', 'DELETE', 'POST'])
@login_required
def delete_category(id):
    # TODO: create function that creates dict based on necessity of edit before delete
    # TODO: pass the dict in a way the edit template can interpret and adapt to display only necessary form fields
    # TODO: simplify delete_afterwards parameter
    current_category = db.session.scalar(sa.select(Category).where(id == Category.id))
    dla = {}
    if current_category.gidguds: dla['g']=True
    if current_category.children: dla['c']=True
    app.logger.info(f'dla before passing to edit route: {dla}')
    #delete_afterwards = True
    if current_category.name == 'default':
        flash('The default Category may not be deleted')
        return redirect(url_for('user_categories', username=current_user.username))
    #elif current_category.gidguds or current_category.children:
    #    flash('This Category has attached GidGuds or Subcategories. Please reassign before deletion.')
    #    return redirect(url_for('edit_category', id=id, delete_afterwards=delete_afterwards))
    elif dla:
        flash('This Category has attached GidGuds or Subcategories. Please reassign before deletion.')
        return redirect(url_for('edit_category', id=id, dla=dla))
    else:
        db.session.delete(current_category)
        db.session.commit()
        flash('Category deleted!')
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