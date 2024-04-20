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

# Flaskform

## DataListField I

    class CreateGudForm(FlaskForm):
    body = StringField('Task', validators=[DataRequired(), Length(min=1, max=140)])
    category = DatalistField('Category')
    submit = SubmitField('Create Gud')

    def __init__(self, category_choices=[], *args, **kwargs):
        super(CreateGudForm, self).__init__(*args, **kwargs)
        # Initialize category choices using the provided argument
        self.category.datalist = category_choices

    @app.route('/create_gud', methods=['GET', 'POST'])
    @login_required
    def create_gud():
        form = CreateGudForm()

        # Retrieve category choices dynamically here
        category_choices = get_category_choices()

        # Pass category_choices to form instantiation
        form = CreateGudForm(category_choices=category_choices)

        if form.validate_on_submit():
            # Process form submission
            pass

        return render_template('create_gud.html', title='Create Gud', form=form)

## DataListField II

You create a simple StringField in your view.

    autocomplete_input = StringField('autocomplete_input', validators=[DataRequired()])

In your template you call the field and add the list parameter (remember to pass the entries to your template):

    {{form.autocomplete_input(list="id_datalist")}}
    <datalist id="id_datalist">
    {% for entry in entries %}
    <option value={{ entry }}>
    {% endfor %}
    </datalist>

## DataListField III

I had the same question; but no answer. After struggling for a while, I have got it to work. forms.py:

    class fiscalYearForm(FlaskForm):
        fy_timeframe = SelectField(
            "Please Select Fiscal Quarter",
            choices=[
                ('FY2022 Q4', 'FY2022 Q4'),
                ('FY2022 Q3', 'FY2022 Q3'),
                ('FY2022 Q2', 'FY2022 Q2'),
                ('FY2022 Q1', 'FY2022 Q1'),
            ],
            validators=[DataRequired()],
        )

html file:

    <form action="" method="post">
        {{ form.hidden_tag() }}
        <div class="mb-3">
            {{ form.fy_timeframe.label(class="form-label") }}
            <input class="form-control" list="fylistOptions" placeholder="Type to search...">
            <datalist id="fylistOptions">
                    {{form.fy_timeframe(class="form-control form-control-sm")}}
            </datalist>
        </div>
        <div class="mb-3">
            {{ form.submit(class="btn btn-primary" }}
        </div>
    </form>

This worked for me. Hope it helps someone.