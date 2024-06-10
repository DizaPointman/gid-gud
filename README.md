/* cSpell:disable */

# Fun

C_Man and G_Man and U_Man as handlers/managers
C_Man.create_child()
C-Man.inject()

# FIXME: maybe add [all_ancestors] and/or [all_descendants] as field or auxiliary table to avoid blacklist recursion

# TODO: GidGud Manager
- implement completed table
- implement necessary functions
- implement create GidGud(body, user, rec 3x), set rec_next on creation
- implement update GidGud, archive old, create new
- implement recurrence, rec_val/rec_unit = None, rec_val/rec_unit = 0/days, rec_val/rec_unit = user defined
- implement complete, if rec_val/rec_unit is None: archive and add to complete, else set rec_next and add to complete
# TODO: GidGud Schedule
- implement simple/advance view parameter for create/edit gidgud route/template
- display form fields depending on view param, use hidden and defaults
- change button label depending on view param (simple/advance)
- simple view: body, category, repeat checkbox
- advanced view: simple + rec_val/rec_unit
- on view change display flash 'changes not saved'
- discard, view, apply buttons as submitfield
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


# Perplexity

class Category(db.Model):
    id = so.mapped_column(sa.Integer, primary_key=True)
    name = so.mapped_column(sa.String(20))
    user_id = so.mapped_column(sa.Integer, db.ForeignKey('user.id'))
    user = so.relationship('User', back_populates='categories')
    depth = so.mapped_column(sa.Integer)
    height = so.mapped_column(sa.Integer)
    parent_id = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), nullable=True)
    parent = so.relationship('Category', remote_side=[id])
    children = so.relationship('Category', back_populates='parent', remote_side=[parent_id], uselist=True)
    gidguds = so.relationship('GidGud', back_populates='category')

    MAX_HEIGHT = 5

    def __repr__(self):
        return f'<Category {self.name}>'

    def __init__(self, name, user=None, parent=None):
        self.name = name
        self.user = user or current_user
        self.parent = parent or Category.create_default_root_category(current_user)
        self.update_depth_and_height()

        @staticmethod
    def create_default_root_category(user):
        # Check if the default category exists for the given user
        default_category = Category.query.filter_by(name='default', user_id=user.id).first()

        # If the default category does not exist, create and return it
        if not default_category:
            default_category = Category(name='default', user=user, depth=0, height=Category.MAX_HEIGHT)
            db.session.add(default_category)
            db.session.commit()

        # Return the existing or newly created default category
        return default_category

    def update_depth_and_height(self):
        # Simplified update logic to prevent unnecessary recursive updates
        if self.parent is None:
            self.depth = 0
            self.height = Category.MAX_HEIGHT
        else:
            self.depth = self.parent.depth + 1
            self.height = 1 if not self.children else max(child.height for child in self.children) + 1
            # Update parent height only if necessary
            if self.parent.height <= self.height:
                self.parent.height = self.height + 1
                self.parent.update_height()

    def get_possible_children(self):
        blacklist = self.generate_blacklist_ancestors()
        return [category for category in self.user.categories if category not in blacklist and self.depth + category.height <= Category.MAX_HEIGHT]

    def generate_blacklist_ancestors(self):
        # More efficient ancestor generation using set comprehension
        return {ancestor for ancestor in self.iterate_ancestors()}

    def iterate_ancestors(self):
        # Generator to iterate through ancestors
        current = self
        while current.parent:
            yield current.parent
            current = current.parent

    def get_possible_parents(self):
        blacklist = self.generate_blacklist_descendants()
        return [category for category in self.user.categories if category not in blacklist and self.height + category.depth <= Category.MAX_HEIGHT]

    def generate_blacklist_descendants(self):
        # Use set comprehension for more concise code
        descendants = {descendant for descendant in self.iterate_descendants(self)}
        descendants.add(self)
        return descendants

    def iterate_descendants(self, category):
        # Generator to iterate through descendants
        for child in category.children:
            yield child
            yield from self.iterate_descendants(child)