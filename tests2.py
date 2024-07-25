# tests/test_models.py

import pytest
from app.models import User, Category
from app.managers.content_manager import ContentManager
from sqlalchemy.exc import IntegrityError

# tests/conftest.py
import pytest
from app.factory import create_app
from app.models import db, User, Category

@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app('config.TestingConfig')

    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # this is where the testing happens!

    ctx.pop()

@pytest.fixture(scope='module')
def init_database():
    # Create the database and the database table(s)
    db.create_all()

    # Insert user data
    user1 = User(username='testuser', email='testuser@example.com')
    user1.set_password('Password123')
    db.session.add(user1)

    # Insert category data
    category1 = Category(name='root', user=user1, parent_id=None)
    db.session.add(category1)

    # Commit the changes for the users
    db.session.commit()

    yield db  # this is where the testing happens!

    db.drop_all()

# tests/test_factory.py
def test_create_app():
    from app.factory import create_app
    app = create_app()
    assert app is not None
    assert app.config['TESTING'] is False

# tests/test_models.py
def test_user_model(init_database):
    from app.models import User

    user = User.query.filter_by(username='testuser').first()
    assert user is not None
    assert user.check_password('Password123') is True

def test_category_model(init_database):
    from app.models import Category

    category = Category.query.filter_by(name='root').first()
    assert category is not None
    assert category.name == 'root'
    assert category.user.username == 'testuser'

# tests/test_routes.py
def test_create_category_get(test_client):
    response = test_client.get('/create_category')
    assert response.status_code == 200
    assert b"Create Category" in response.data

def test_create_category_post(test_client, init_database):
    response = test_client.post('/create_category', data=dict(
        name='New Category',
        submit=True
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"New Category created!" in response.data

# tests/test_content_manager.py
def test_cat_get_or_create_root(init_database):
    from app.managers.content_manager import ContentManager
    from app.models import User

    user = User.query.filter_by(username='testuser').first()
    c_man = ContentManager()
    root = c_man.cat_get_or_create_root(user)
    assert root is not None
    assert root.name == 'root'
    assert root.user == user

def test_cat_create_from_form(init_database):
    from app.managers.content_manager import ContentManager
    from app.models import User, Category

    user = User.query.filter_by(username='testuser').first()
    c_man = ContentManager()
    form_data = {'name': 'Test Category', 'user': user}
    category = c_man.cat_create_from_form(form_data)
    assert category is not None
    assert category.name == 'Test Category'
    assert category.user == user

def test_new_user(init_database):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, password, and role fields are defined correctly
    """
    user = User(username='testuser', email='test@test.com')
    user.set_password('testpassword')
    assert user.username == 'testuser'
    assert user.email == 'test@test.com'
    assert user.password_hash != 'testpassword'
    assert user.check_password('testpassword')

def test_user_representation(init_database):
    """
    GIVEN an existing User
    WHEN the User is represented as a string
    THEN check the representation is correct
    """
    user = User.query.filter_by(username='testuser').first()
    assert str(user) == '<User testuser>'

def test_new_category(init_database):
    """
    GIVEN a Category model
    WHEN a new Category is created
    THEN check the name and user fields are defined correctly
    """
    user = User.query.filter_by(username='testuser').first()
    category = Category(name='Test Category', user=user)
    assert category.name == 'Test Category'
    assert category.user == user

def test_category_representation(init_database):
    """
    GIVEN an existing Category
    WHEN the Category is represented as a string
    THEN check the representation is correct
    """
    category = Category.query.filter_by(name='root').first()
    assert str(category) == '<Category root>'

def test_category_path_validation(init_database):
    """
    GIVEN a Category model
    WHEN a path is set
    THEN check that the path validation works correctly
    """
    category = Category.query.filter_by(name='root').first()
    category.path = '1.2.3'
    assert category.path == '1.2.3'
    
    with pytest.raises(ValueError):
        category.path = 'invalid.path'

def test_category_depth(init_database):
    """
    GIVEN a Category with a path
    WHEN the depth property is accessed
    THEN check that it returns the correct depth
    """
    category = Category.query.filter_by(name='root').first()
    category.path = '1.2.3'
    assert category.depth == 3

def test_category_parent_child_relationship(init_database):
    """
    GIVEN a Category model
    WHEN parent-child relationships are established
    THEN check that the relationships are correct
    """
    user = User.query.filter_by(username='testuser').first()
    parent = Category(name='Parent', user=user)
    child = Category(name='Child', user=user)
    child.set_parent(parent)
    
    assert child.parent == parent
    assert child in parent.get_children()

def test_category_move_subtree(init_database):
    """
    GIVEN a Category hierarchy
    WHEN a subtree is moved
    THEN check that the paths are updated correctly
    """
    user = User.query.filter_by(username='testuser').first()
    root = Category(name='Root', user=user)
    parent = Category(name='Parent', user=user)
    child = Category(name='Child', user=user)
    
    parent.set_parent(root)
    child.set_parent(parent)
    
    new_parent = Category(name='New Parent', user=user)
    new_parent.set_parent(root)
    
    Category.move_subtree(parent.id, new_parent.id)
    
    assert parent.path.startswith(f"{new_parent.path}.")
    assert child.path.startswith(parent.path)

# tests/test_content_manager.py

def test_cat_get_or_create_root(init_database):
    """
    GIVEN a ContentManager and a User
    WHEN cat_get_or_create_root is called
    THEN check that a root category is created or retrieved
    """
    user = User.query.filter_by(username='testuser').first()
    c_man = ContentManager()
    root = c_man.cat_get_or_create_root(user)
    
    assert root is not None
    assert root.name == 'root'
    assert root.user == user
    assert root.parent_id is None

def test_cat_create_from_form(init_database):
    """
    GIVEN a ContentManager and form data
    WHEN cat_create_from_form is called
    THEN check that a new category is created correctly
    """
    user = User.query.filter_by(username='testuser').first()
    c_man = ContentManager()
    form_data = {'name': 'Test Category', 'user': user}
    category = c_man.cat_create_from_form(form_data)
    
    assert category is not None
    assert category.name == 'Test Category'
    assert category.user == user
    assert category.parent.name == 'root'

def test_cat_create_duplicate_name(init_database):
    """
    GIVEN a ContentManager and existing categories
    WHEN cat_create_from_form is called with a duplicate name
    THEN check that an IntegrityError is raised
    """
    user = User.query.filter_by(username='testuser').first()
    c_man = ContentManager()
    form_data = {'name': 'Duplicate Category', 'user': user}
    c_man.cat_create_from_form(form_data)
    
    with pytest.raises(IntegrityError):
        c_man.cat_create_from_form(form_data)

# Additional tests for routes can be added in tests/test_routes.py