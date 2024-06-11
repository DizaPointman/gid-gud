/* cSpell:disable */

# old model functions

## category

    class Category(db.Model):

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(20))
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, db.ForeignKey('user.id'))
    user: so.Mapped['User'] = so.relationship('User', back_populates='categories')
    level: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    parent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), nullable=True)
    parent: so.Mapped[Optional['Category']] = so.relationship('Category', remote_side=[id])
    children: so.Mapped[list['Category']] = so.relationship('Category', back_populates='parent', remote_side=[parent_id], uselist=True)
    gidguds: so.Mapped[Optional[list['GidGud']]] = so.relationship('GidGud', back_populates='category')

    def __repr__(self):
        return '<Category {}>'.format(self.name)

    def assign_category_levels_with_depth_limit(root_category, max_depth):
        queue = [(root_category, 0)]  # Initialize queue with root category and its level
        visited = set()  # Set to keep track of visited categories

        while queue:
            category, level = queue.pop(0)  # Dequeue a category from the queue
            category.level = level  # Update the level of the category

            visited.add(category)  # Mark the category as visited

            if level < max_depth:  # Limit the depth of traversal
                # Enqueue children of the current category with their respective levels
                for child in category.children:
                    if child not in visited:
                        queue.append((child, level + 1))

    # Example usage with depth limit of 3:
    root_category = Category.query.filter_by(parent_id=None).first()  # Assuming there is only one root category
    assign_category_levels_with_depth_limit(root_category, max_depth=3)

    def get_max_child_level(self):

                # Define the recursive Common Table Expression (CTE)
        cte = db.session.query(
            Category.id.label('category_id'),
            Category.level.label('max_level')
        ).filter(Category.parent_id == self.id)

        recursive_cte = cte.cte(recursive=True)

        # Recursive query to traverse the category hierarchy
        recursive_query = recursive_cte.union_all(
            sa.select([
                Category.id,
                sa.func.coalesce(sa.func.max(recursive_cte.c.max_level), 0)
            ]).where(Category.parent_id == recursive_cte.c.category_id)
        )

        # Retrieve the maximum level attained by the children categories
        max_child_level = db.session.query(sa.func.max(recursive_query.c.max_level)).scalar()

        # Output the highest level attained by the children categories
        print("Highest level of children categories:", max_child_level)

    def update_level(self):
        if self.name == 'default':
            # Assure default category level is always 0
            pass
        else:
            # Update the level of the category based on the maximum level among its children
            max_child_level_query = db.session.query(sa.func.max(Category.level)).filter(Category.parent_id == self.id).scalar()
            self.level = (max_child_level_query or 0) + 1

    def get_possible_children_and_parents(self) -> dict:
        # Retrieve possible children and parents based on level constraints
        possible_children_query = db.session.query(Category.id, Category.name, Category.level)\
            .filter(or_(Category.level < self.level, (Category.level + self.level) <= 3))\
            .filter(Category.name != 'default')\
            .filter(Category.id != self.id)

        # FIXME: need additional condition for possible children, currently bottom child has level 1 and therefore is considered a possible parent
        # need to check parents upwards instead
        possible_parents_query = db.session.query(Category.id, Category.name, Category.level)\
            .filter(or_(Category.level > self.level, (Category.level + self.level) <= 3))\
            .filter(Category.id != self.id)

        possible_children = {'possible_children': [{'id': category.id, 'name': category.name, 'level': category.level} for category in possible_children_query]}
        possible_parents = {'possible_parents': [{'id': category.id, 'name': category.name, 'level': category.level} for category in possible_parents_query]}

        return {**possible_children, **possible_parents}

    def get_all_children(self) -> dict:
        # Retrieve all children of the category
        all_children_query = db.session.query(Category.id, Category.name, Category.level).filter(Category.parent_id == self.id)
        all_children = {'all_children': [{'id': category.id, 'name': category.name, 'level': category.level} for category in all_children_query]}
        return all_children

    def get_selection_possible_parents(self, max_level: int) -> dict:
        # Retrieve possible parents for selected children based on the maximum level among the children
        possible_parents_query = db.session.query(Category.id, Category.name, Category.level)\
            .filter(or_(Category.level > max_level, (Category.level + max_level) <= 3))
        selection_possible_parents = {'selection_possible_parents': [{'id': category.id, 'name': category.name, 'level': category.level} for category in possible_parents_query]}
        return selection_possible_parents

    def get_tree_depth(self):
        """
        Recursively calculate the depth of the category tree starting from this category.

        Returns:
            int: The depth of the category tree.
        """
        if not self.children:  # Base case: if the category has no children, return 0
            return 0
        else:
            # Recursively calculate the depth of each child and find the maximum depth
            max_child_depth = max(child.get_tree_depth() for child in self.children)
            return 1 + max_child_depth  # Increment depth by 1 for the current category

    def get_tree_height(self):

        if self.parent == None or self.parent.name == 'default':
            return 0

        else:
            max_parent_height = self.parent.get_tree_height()
            return 1 + max_parent_height

    def get_possible_parents(self) -> list[dict]:
        """
        Get a list of possible parent categories based on the category tree depth.

        Returns:
            list[dict]: A list of dictionaries containing category IDs and names.
        """
        possible_parents = []

        tree_depth = self.get_tree_depth()

        # Base query to select all categories except the current one
        base_query = (
            db.session.query(Category.id, Category.name)
            .filter(Category.id != self.id)
        )

        if tree_depth == 2:
            # No parent possible except 'default'
            categories_query = base_query.filter(Category.name == 'default')

        elif tree_depth == 1:
            # Parent without grandparent possible, only 'default' category as grandparent allowed
            categories_query = base_query.filter(~Category.parent.has(parent_id=None))

        else:  # tree_depth == 0
            # Parent with grandparent possible, only 'default' category as great grandparent allowed
            categories_query = base_query.filter(~Category.parent.has(Category.parent.has(parent_id=None)))

        possible_parents = [{'id': category_id, 'name': category_name} for category_id, category_name in categories_query]
        return possible_parents

    def get_possible_children(self) -> list[dict]:

        # TODO: adjust queries to work like utils function

        possible_children = []

        tree_height = self.get_tree_height()

        if tree_height == 2:
            return possible_children

        base_query = (
            db.session.query(Category.id, Category.name)
            .filter(Category.id != self.id)
            .filter(Category.name != 'default')
        )

        if tree_height == 1:
            categories_query = base_query.filter(Category.children == None)

        else:
            categories_query = base_query.filter(~Category.children.any(Category.children != None))

        possible_children = [{'id': category_id, 'name': category_name} for category_id, category_name in categories_query]
        return possible_children

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
        current_app.logger.info(f"field data - if field.data is None or 'instantly': {field.data in (None, 'instantly')}")
        if field.data in (None, 'instantly'):
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

# Flaskform

# SelectField with Input

In our esteemed context, Bootstrap alone does not inherently provide a direct mechanism to combine a StringField with a SelectField. However, fear not, for within the realm of Flask-WTF and Jinja2 templating, we possess the power to craft such combinations with elegance and finesse.

To achieve this, we can utilize Flask-WTF's FormField and FieldList to create custom composite fields. You can define a WTForms form class that encapsulates both a StringField and a SelectField, then render these fields within your Jinja2 template using appropriate Bootstrap styling.

Here's a basic example to illustrate the concept:

    python

    from flask_wtf import FlaskForm
    from wtforms import StringField, SelectField, FormField, FieldList

    class CustomForm(FlaskForm):
        string_field = StringField('String Field')
        select_field = SelectField('Select Field', choices=[('1', 'Option 1'), ('2', 'Option 2')])

    class MainForm(FlaskForm):
        custom_field = FormField(CustomForm)

    # In your Flask view function
    @app.route('/example', methods=['GET', 'POST'])
    def example():
        form = MainForm()
        if form.validate_on_submit():
            # Handle form submission
            pass
        return render_template('example.html', form=form)

In your Jinja2 template (example.html), you can then render the custom composite field using Bootstrap styling:

    html

    <form method="POST">
        {{ form.csrf_token }}
        <div class="form-group">
            <label for="custom_field_string_field">String Field</label>
            <input type="text" class="form-control" id="custom_field_string_field" name="custom_field.string_field">
        </div>
        <div class="form-group">
            <label for="custom_field_select_field">Select Field</label>
            <select class="form-control" id="custom_field_select_field" name="custom_field.select_field">
                {% for value, label in form.custom_field.select_field.choices %}
                    <option value="{{ value }}">{{ label }}</option>
                {% endfor %}
            </select>
        </div>
        <button type="submit" class="btn btn-primary">Submit</button>
    </form>

By employing this approach, you can seamlessly integrate a StringField with a SelectField in accordance with the Bootstrap styling conventions, harmonizing form elements with grace and precision. Should further guidance be needed, do not hesitate to beckon!



# Formdata Example

[Markup('<input id="name" maxlength="20" minlength="1" name="name" required type="text" value="cman test 568">'),

Markup('<select id="parent" name="parent"><option selected value="root">root</option><option selected value="root">root</option><option value="testcategoryformdata">testcategoryformdata</option><option value="health">health</option><option value="features3">features3</option></select>'),

Markup('<select id="reassign_gidguds" name="reassign_gidguds"><option selected value="No GidGuds">No GidGuds</option></select>'),

Markup('<select id="reassign_children" name="reassign_children"><option selected value="No Children">No Children</option></select>'),

Markup('<input id="submit" name="submit" type="submit" value="Save Changes">'),

Markup('<input id="csrf_token" name="csrf_token" type="hidden" value="Ijg3ZTFlNzcwMjFjY2UzZmQ2NzkxYjg2ZmVjNWM1ZTlmYjdmMjlmMDMi.Zl2nMA.-FGeszgJ6dYatzeKlArp0BAIxSo">')]