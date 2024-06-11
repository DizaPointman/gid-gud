/* cSpell:disable */

# Fun

C_Man and G_Man and U_Man as handlers/managers
C_Man.create_child()
C-Man.inject()

# FIXME: maybe add [all_ancestors] and/or [all_descendants] as field or auxiliary table to avoid blacklist recursion

# TODO: GidGud Manager
- add materialized path to category and gidgud models
- update category methods in cm
- add materialized path handling to archive functions for gidgud and category
# TODO: GidGud Schedule
- implement simple/advance view parameter for create/edit gidgud route/template
- display form fields depending on view param, use hidden and defaults
- change button label depending on view param (simple/advance)
- simple view: body, category, repeat checkbox
- advanced view: simple + rec_val/rec_unit
- on view change display flash 'changes not saved'
- discard, view, apply buttons as submitfield
# TODO: handle archived objects
- added archived_at as blacklisted for possible parents, children, parents for selection
- need some general handling, a decorator?
- somehow flag archived_at items as excluded from rest of logic
# TODO: Tests for GidGud Manager
# TODO: Tests for routes
# TODO: implement add children function with multiple selectfield


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
