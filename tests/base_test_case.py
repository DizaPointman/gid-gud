import os
import sys
import unittest
import pytest
from datetime import datetime, timezone, timedelta
from functools import wraps
from pytz import utc

# Ensure the app module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.managers.content_manager import ContentManager
from app.factory import create_app, db
from app.models import Category, CompletionTable, User, GidGud

os.environ['DATABASE_URL'] = 'sqlite://'

class BullshitGenerator():

    # TODO: add user gen
    # TODO: add gidgud gen
    # TODO: add completion gen

    def __init__(self, c_man):
        self.c_man = c_man

    def test_bs(self):
        alive = "Bullshit generator is alive"
        print(alive)
        return alive

    def gen_cat_tree(self, user=None, tree_height=None):

        # Generate tree for tree_height = 6
        # 'root'
        # 'root' -> 'cat1'
        # 'root' -> 'cat2' -> 'cat22'
        # 'root' -> 'cat3' -> 'cat33' -> 'cat333'
        # 'root' -> 'cat4' -> 'cat44' -> 'cat444' -> 'cat4444'
        # 'root' -> 'cat5' -> 'cat55' -> 'cat555' -> 'cat5555' -> 'cat55555'

        if not user:
            raise ValueError("BullshitGenerator needs a user")
        if not tree_height:
            tree_height = Category.MAX_HEIGHT
        categories = []
        root = Category(name='root', user=user, parent=None)
        categories.append(root)

        for j in range(1, tree_height + 1):
            for i in range(1, j + 1):
                cat_name = 'cat' + (str(j) * i)
                parent = root
                category = Category(name=cat_name, user=user, parent=parent)
                categories.append(category)
                if i != j:
                    parent = category
            parent = root

        return categories

@pytest.mark.usefixtures("test_client", "init_database")
class BaseTestCase(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, test_client, init_database):
        self.test_client = test_client
        self.db = init_database

    def setUp(self):
        self.app = create_app('config.TestingConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Initialize ContentManager instance
        self.c_man = ContentManager()
        # initialize BullshitGenerator instance
        self.bs = BullshitGenerator(self.c_man)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
