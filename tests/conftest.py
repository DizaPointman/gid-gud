# tests/conftest.py
import pytest
from app.factory  import create_app, db
from app.models import User, Category


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