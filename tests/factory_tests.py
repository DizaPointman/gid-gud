from flask import current_app
import pytest
from app.factory import create_app
from tests.base_test_case import BaseTestCase
from app.factory import db

class FactoryCase(BaseTestCase):

    print("Test: FactoryCase")

    def test_create_app(self):
        app = create_app()
        assert app is not None
        assert app.config['TESTING'] is False

    def test_app_is_testing(self):
        app = create_app('config.TestingConfig')
        with app.app_context():
            self.assertTrue(current_app.config['TESTING'])

    def test_app_is_production(self):
        app = create_app('config.ProductionConfig')
        with app.app_context():
            self.assertTrue(current_app.config['SECRET_KEY'] is not None)
            self.assertFalse(current_app.config['DEBUG'])

    def test_app_has_db(self):
        app = create_app('config.TestingConfig')
        with app.app_context():
            self.assertIsNotNone(db)

    def test_blueprints_registration(self):
        app = create_app('config.TestingConfig')
        with app.app_context():
            self.assertIn('main', app.blueprints)
            self.assertIn('auth', app.blueprints)

# This is optional if you want to run this file directly
#if __name__ == '__main__':
#    pytest.main(['-v', __file__])