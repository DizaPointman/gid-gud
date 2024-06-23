/* cSpell:disable */

# Fun

C_Man and U_Man as handlers/managers
C_Man.create_child()
C-Man.inject()

# Flatting Comprehensions
The "expression" applies to the inner_var, not the outer_var
You can only have one expression at the beginning, but this expression can use any of the variables defined in the subsequent for clauses

    {expression for outer_var in outer_iterable for inner_var in inner_iterable}

    flat_collection = {
            expression
            for outer_var in outer_iterable
            for inner_var in inner_iterable
        }

    {expression for outer_var in outer_iterable for middle_var in middle_iterable for inner_var in inner_iterable}

    flat_collection = {
            expression (inner_var * outer_var)
            for outer_var in outer_iterable
            for middle_var in middle_iterable
            for inner_var in inner_iterable
        }

    blacklist_ids = {
            int(id)
            for path in blacklist_paths
            for id in path.split('.')[:-max_depth_children]
        }

    blacklist_ids = {int(id) for path in blacklist_paths for id in path.split('.')[:-max_depth_children]}




# TODO: Tests for Content Manager
# TODO: Tests for Routes

# TODO: Implement Materialized Path
## Models
### Category
- funcs in draft
## Content Manager
- funcs in draft
- adapt create/update from form to use {id, name}
## Routes
- modify choices to use {id, name}
## Template
- modify category tree makro

# TODO: Simplify Content Manager
- remove Versioning
- only archived/not archived
## Category
- change name
- change parent
- reassign/remove children
- reassign gidguds
- Funcs: create(data), create_from_form(form), get_or_create(name), create_from_batch(form), update(data)
## GidGud
- change name
- change category
- change recurrence
- complete
- Funcs: create(data), create_from_form(form), create_from_batch(form), update(data), complete




# Security

## Requests

### CSRF

I'm going to implement them as POST requests, which are triggered from the web browser as a result of submitting a web form.
It would be easier to implement these routes as GET requests, but then they could be exploited in CSRF attacks.
Because GET requests are harder to protect against CSRF, they should only be used on actions that do not introduce state changes.
Implementing these as a result of a form submission is better because then a CSRF token can be added to the form.

CSRF: https://en.wikipedia.org/wiki/Cross-site_request_forgery
Guide: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-viii-followers


# Dropdowns
https://hackanons.com/2021/09/flask-dropdown-menu-everything-you-need-to-know.html

# Beauty/Style
https://blog.miguelgrinberg.com/post/beautiful-interactive-tables-for-your-flask-templates

SQLite JSON

https://docs.sqlalchemy.org/en/13/dialects/sqlite.html#sqlalchemy.dialects.sqlite.JSON
https://docs.sqlalchemy.org/en/13/core/type_basics.html#sqlalchemy.types.JSON.JSONElementType
https://stackoverflow.com/questions/75379948/what-is-correct-mapped-annotation-for-json-in-sqlalchemy-2-x-version

https://amercader.net/blog/beware-of-json-fields-in-sqlalchemy/

# FlaskForm / WTForm

Default for SelectField

https://stackoverflow.com/questions/12099741/how-do-you-set-a-default-value-for-a-wtforms-selectfield/12100214#12100214
https://wtforms.readthedocs.io/en/2.3.x/fields/

# Structure

your_app/
│
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── category.py
│   ├── managers/
│   │   ├── __init__.py
│   │   └── category_manager.py
│   ├── sessions/
│   │   ├── __init__.py
│   │   └── session_manager.py
│   ├── events/
│   │   ├── __init__.py
│   │   └── event_manager.py
│   ├── templates/
│   ├── static/
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── user/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── templates/
│   │   ├── dashboard/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── templates/
│   │   └── auth/
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       └── templates/
│   └── utils/
│       ├── __init__.py
│       ├── auth.py
│       └── decorators.py
│
├── migrations/
│
├── tests/
│   ├── __init__.py
│   ├── test_user.py
│   ├── test_category_manager.py
│   ├── test_session_manager.py
│   └── test_event_manager.py
│
├── config.py
├── manage.py
└── requirements.txt


# Git

## Rewind and Reset

https://www.30secondsofcode.org/git/s/rewind-to-commit/

## Amend

git commit --amend --no-edit

## Git Flow

Semantic Versioning is used

INFO: there's also a special versioning for python!!!!

https://jeffkreeftmeijer.com/git-flow/

### Changelog

https://mokkapps.de/blog/how-to-automatically-generate-a-helpful-changelog-from-your-git-commit-messages
https://dev.to/devsatasurion/automate-changelogs-to-ease-your-release-282

### Cheatsheet

https://danielkummer.github.io/git-flow-cheatsheet/
https://www.baeldung.com/cs/semantic-versioning

Correct commit msg

https://www.conventionalcommits.org/en/v1.0.0/
https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines

Git Tag

https://git-scm.com/book/en/v2/Git-Basics-Tagging

### Features

1. git flow feature start [feature name]
2. git flow feature finish [feature name]

### Versioned releases

1. git flow release start 0.1.0
2. git flow release finish '0.1.0'

### Hotfixing production code

1. git flow hotfix start [assets]
2. git flow hotfix finish 'assets'

# Working Strategy

## 1.0

do this for ONE functionality

1. FlaskForm with minimum
2. html template
3. route
4. utils function/s

REPEAT or alter existing for EACH additional feature

## Helpful

    # TODO: Implement error handling here
    # FIXME: This function is not optimized
    # BUG: This block needs refactoring

# Easter Eggs

TabNine Pro 90 days free trial

## PROBLEM

### Next feature



### Possible features

1. CSS via bootstrap or tailwind. 
- UI redesign. 
- Light and dark mode. 
- Better form field for timer
- 69:69 / days:hours / Monthly:weekly / Every X of Y

1. Input sanitation and flash handler. 

2. Creation of test library. 
- Integrate profiling. 
- Existing library Or create package. 
- Possibility to measure routes or functions. 
- Want to out a measure for Memory. Execution time Database queries 
- Optimization of eager and lazy loading 
- Optimizing request types for routes. 

1. Add amount unit and times to gidgud. 
- Let user create templates. 
- Favorite templates 
- Statistics page optical overhaul. 
- Advanced filters and data display 

1. Avatars 
- Implement avatar progression 
- One avatar or different avatars depending on category.

1. Integration of other platform studs via API 

2. User options. 
- UI customization. 
- Cringe mode - Good girl. Good boy 

1. Task breaker 

2. Correct read me and implement development log 

# Caching

Caching the Object:

    Edit Route: When the user navigates to the update route, query the object by its ID and store it in a cache. You can use Flask's session object, a caching library like Flask-Cache, or a global dictionary to store the cached objects.

    Update Function: In your update function, accept the object ID along with the form data. Instead of querying the database again for the object, retrieve it from the cache using its ID.

Example Implementation:

    python

    from flask import session

    # Edit Route
    @app.route('/edit/<int:id>', methods=['GET'])
    def edit(id):
        # Query object by ID and store it in the session
        obj = YourModel.query.get(id)
        session['cached_object'] = obj
        # Render the edit form with the object data
        return render_template('edit.html', obj=obj)

    # Update Function
    @app.route('/update', methods=['POST'])
    def update():
        # Get the object ID from the form data
        id = request.form.get('id')
        # Retrieve the object from the session cache
        obj = session.get('cached_object')
        if obj:
            # Update object attributes based on form data
            obj.attribute = request.form.get('attribute')
            # Commit changes to the database
            db.session.commit()
            # Optionally, remove the object from the cache
            session.pop('cached_object')
            # Redirect to a success page or render a success message
            return redirect(url_for('success'))
        else:
            # Handle error: Object not found in cache
            return render_template('error.html', message='Object not found in cache')

Considerations:

    Cache Expiration: You may want to set an expiration time for the cached object to prevent stale data. For example, you could refresh the cache periodically or invalidate it after a certain period of inactivity.

    Cache Size: Be mindful of memory usage when caching objects, especially if your application deals with a large number of concurrent users or frequently updated data.

    Query Optimization: If the performance impact of querying twice is negligible and the separation of concerns is a primary concern, you may opt to query the database twice instead of caching the object. However, if minimizing database queries is critical for performance, caching can be a viable solution.

    Database Load: Monitor the number of database queries and overall database load to ensure that caching is effectively reducing the query load without introducing significant overhead.

In summary, caching the object in the session or another caching mechanism can help reduce the number of database queries and improve performance while maintaining separation of concerns in your application. However, be mindful of cache expiration, memory usage, and overall impact on performance and scalability.

# Enhancements and Best Practices

    Session Management Enhancement:
        To ensure session consistency, consider using a context manager for session handling if not already in place.

    python

    from contextlib import contextmanager

    @contextmanager
    def session_scope():
        """Provide a transactional scope around a series of operations."""
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# Usage
    with session_scope() as session:
        old_gidgud = session.query(GidGud).get(old_id)
        changes = map_form_to_object_changes(old_gidgud, form)
        new_gidgud = old_gidgud.archive_and_recreate(changes)

Handling Relationships:

    If your object has relationships that need to be duplicated, extend the duplicate method to handle these appropriately.

    python

    def duplicate(self, changes=None):
        new_data = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        new_data.pop('id', None)
        if changes:
            new_data.update(changes)
        new_instance = self.__class__(**new_data)
        
        # Handle relationships if necessary
        # Example: new_instance.related_objects = [rel.duplicate() for rel in self.related_objects]
        
        return new_instance

Unique Constraints Handling:

    Ensure that changes dictionary updates unique fields where necessary to avoid constraint violations.

Detailed Logging:

    Implement logging within the archive_and_recreate method to track changes and operations for audit purposes.

    python

    import logging

    logger = logging.getLogger(__name__)

    def archive_and_recreate(self, changes):
        new_gidgud = self.duplicate(changes)
        
        if self.a_history_of_violence:
            new_gidgud.a_history_of_violence = f"{self.a_history_of_violence}/{new_gidgud.id}"
        else:
            new_gidgud.a_history_of_violence = f"{self.id}/{new_gidgud.id}"
        
        self.archived_at = datetime.utcnow()
        session.add(new_gidgud)
        session.commit()
        
        logger.info(f'Archived GidGud {self.id} and created new GidGud {new_gidgud.id} with changes: {changes}')
        
        return new_gidgud

By considering these potential disadvantages and enhancements, you can ensure that your implementation is robust, maintainable, and efficient.

# Current_User

Stack: Flask, SQLAlchemy, SQLite

I want to create a function parse_form that parses formdata that was sent from my routes. The function will reside in my content_manager class. Is it a problem if parse_form makes use of Flasks current_user by adding user_id=current_user.id? The idea is, that I don't have to send the user id to the backend for everything. But I'm hesitant, since I am unsure if this could provide a security problem
Answer
Security Considerations
Using Flask's current_user in your parse_form function is generally not a security problem, as long as you follow some best practices. However, it's important to understand the potential risks and take appropriate measures to mitigate them.
Potential Risks

    Cross-Site Request Forgery (CSRF): If your application is vulnerable to CSRF attacks, an attacker could potentially submit a form with a different user's session, leading to unauthorized actions being performed on behalf of that user.
    Session Hijacking: If an attacker manages to hijack a user's session (e.g., through session fixation or session stealing), they could potentially perform actions as that user, including submitting forms.

Mitigations

    CSRF Protection: Flask provides built-in CSRF protection, which you should enable for all routes that handle form submissions. This will ensure that only forms submitted from your application are processed, mitigating the risk of CSRF attacks.
    Secure Session Management: Implement secure session management practices, such as using secure cookies (with the HttpOnly and Secure flags), setting appropriate session expiration times, and regenerating sessions after sensitive operations (e.g., login, password change).
    Input Validation: Always validate and sanitize user input, including form data, to prevent various injection attacks (e.g., SQL injection, XSS).
    Principle of Least Privilege: Only grant the necessary permissions and access to the parse_form function and the content_manager class. Ensure that they cannot be accessed or invoked by unauthorized users or from untrusted sources.
    Logging and Monitoring: Implement logging and monitoring mechanisms to detect and respond to potential security incidents or suspicious activities.

Conclusion
Using Flask's current_user in your parse_form function is generally acceptable, as long as you follow security best practices and implement appropriate mitigations. However, it's crucial to thoroughly review your application's security posture, including CSRF protection, session management, input validation, and access control mechanisms, to ensure that your application is secure against various types of attacks.

Industry Standard Approach for Handling User ID in Form Submissions
When dealing with form submissions in a web application, especially when user-specific data is involved, it is crucial to handle user identification securely and efficiently. Here are the industry-standard practices for handling user IDs in form submissions:
1. Use Server-Side Session Management
Instead of sending the user ID with every form submission, leverage server-side session management to keep track of the authenticated user. This approach ensures that the user ID is securely managed and not exposed to potential tampering.

    Flask-Login: Use Flask-Login to manage user sessions. The current_user object provided by Flask-Login can be used to access the authenticated user's information, including the user ID.

python
from flask_login import current_user

def parse_form(formdata):
    user_id = current_user.id
    # Process formdata and associate it with user_id

2. CSRF Protection
Enable CSRF protection to prevent Cross-Site Request Forgery attacks. Flask-WTF provides CSRF protection out of the box.

python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

3. Hidden Fields for User ID (Not Recommended)
While it is possible to include the user ID as a hidden field in the form, this approach is not recommended due to security risks. Users could potentially manipulate the hidden field to impersonate another user.
4. Database Operations
When creating or updating objects in the database, use the user ID from the session (i.e., current_user.id) rather than relying on user-supplied data.

Creating Objects:

    python
    @app.route('/create', methods=['POST'])
    def create_object():
        if request.method == 'POST':
            new_object = MyModel(
                data=request.form['data'],
                user_id=current_user.id
            )
            db.session.add(new_object)
            db.session.commit()
            return redirect(url_for('success'))

Updating Objects:

    python
    @app.route('/update/<int:id>', methods=['POST'])
    def update_object(id):
        obj = MyModel.query.get_or_404(id)
        if obj.user_id != current_user.id:
            abort(403)  # Forbidden
        obj.data = request.form['data']
        db.session.commit()
        return redirect(url_for('success'))

    5. Role-Based Access Control
    Implement role-based access control (RBAC) to ensure that users can only perform actions they are authorized to do. This can be managed using Flask-Security or a custom implementation.

    python
    from flask_security import roles_required

    @app.route('/admin', methods=['GET'])
    @roles_required('admin')
    def admin_dashboard():
        return render_template('admin/dashboard.html')

Example Implementation
Here is a complete example of how to handle form submissions securely using Flask, Flask-Login, and SQLAlchemy:

    python
    from flask import Flask, request, redirect, url_for, render_template
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager, UserMixin, login_user, current_user, login_required
    from flask_wtf.csrf import CSRFProtect

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
    app.config['SECRET_KEY'] = 'your_secret_key'

    db = SQLAlchemy(app)
    login_manager = LoginManager(app)
    csrf = CSRFProtect(app)

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(150), unique=True, nullable=False)
        email = db.Column(db.String(150), unique=True, nullable=False)
        password = db.Column(db.String(150), nullable=False)

    class MyModel(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        data = db.Column(db.String(255), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/create', methods=['GET', 'POST'])
    @login_required
    def create_object():
        if request.method == 'POST':
            new_object = MyModel(
                data=request.form['data'],
                user_id=current_user.id
            )
            db.session.add(new_object)
            db.session.commit()
            return redirect(url_for('success'))
        return render_template('create.html')

    @app.route('/success')
    def success():
        return "Object created successfully!"

    if __name__ == '__main__':
        app.run(debug=True)

Conclusion
By using server-side session management, CSRF protection, and secure database operations, you can ensure that user-specific data is handled securely and efficiently. This approach minimizes the risk of security vulnerabilities and ensures that user IDs are managed in a secure manner.