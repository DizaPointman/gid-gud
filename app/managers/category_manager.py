from flask import current_app
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DatabaseError
from app.utils import log_exception
from app.models import Category
from app.factory import db


# BUG: generate blacklist needs instantiated CategoryManager
#factory.py
#with app.app_context():
#        c_man = CategoryManager()

class CategoryManager:

    MAX_HEIGHT = 5  # Setting a maximum height for categories tree


    def __init__(self, db=None):

        self.db = db

    def test_cm(self):
        return current_app.logger.info("Testing category manager initialization")


    def return_or_create_category(self, name=None, user=None, parent=None):

        try:
            # Start a transaction
            #with self.db.session.begin():

            user = user or current_user

            # BUG: added this for bug hunt
            if not user or not hasattr(user, 'id'):
                raise ValueError("A valid user must be provided")

            # Check if 'root' category exists and create it if not
            root = Category.query.filter_by(name='root', user_id=user.id).first()
            if not root:
                root = Category(name='root', user=user, depth=0, height=CategoryManager.MAX_HEIGHT)
                db.session.add(root)
                db.session.commit()

            # Return 'root' category if no name is provided
            if not name:
                return root

            # Check if category with name exists and return it
            category = Category.query.filter_by(name=name, user_id=user.id).first()

            # If the category with name does not exist, create it
            if not category:

                parent = parent or root
                category = Category(name=name, user=user, parent=parent)
                db.session.add(category)

                # Update parent's depth and height if necessary
                if parent != root:
                    CategoryManager.update_depth_and_height(parent)
                db.session.commit()

            return category

        except SQLAlchemyError as e:
            log_exception(e)
            db.session.rollback()
            return False
        except Exception as e:
            log_exception(e)
            db.session.rollback()
            return False

    def update_depth(self, category):
        if category.parent is not None:
            category.depth = category.parent.depth + 1
            if category.children:
                for child in category.children:
                    CategoryManager.update_depth(child)

    def update_height(self, category):
        if category.parent is not None:
            if not category.children:
                category.height = 1
            else:
                category.height = max(child.height for child in category.children) + 1
                if category.parent.height != category.height + 1:
                    category.parent.update_height(category)

    def update_depth_and_height(self, category):

        if category.parent is not None:
            CategoryManager.update_depth(category)
            CategoryManager.update_height(category)

    def get_possible_children(self, category):

        bl_cat = category
        # Generate blacklist because ancestors can't be children
        blacklist = CategoryManager.generate_blacklist_ancestors(bl_cat)
        # Filter out blacklisted categories and those that would violate MAX_HEIGHT
        return [cat for cat in category.user.categories if cat not in blacklist and cat.depth + cat.height <= CategoryManager.MAX_HEIGHT] or []


    def generate_blacklist_ancestors(self, category):

        # Generate blacklist by adding category and recursively adding parents
        blacklist = set()
        blacklist.add(category)  # Add the initial category
        while category.parent:
            category = category.parent
            blacklist.add(category)
        return blacklist


    def get_possible_parents(self, category):

        bl_cat = category
        # Generate blacklist because descendants can't be parents
        blacklist = CategoryManager.generate_blacklist_descendants(bl_cat)
        # Filter out blacklisted categories and those that would violate MAX_HEIGHT
        return [cat for cat in category.user.categories if cat not in blacklist and cat.height + cat.depth <= CategoryManager.MAX_HEIGHT]


    def generate_blacklist_descendants(self, category):

        # Generate blacklist by adding category and recursively adding children
        blacklist = set()
        blacklist.add(category)  # Add category to the blacklist

        def blacklist_children(cat):
            if cat.children:
                for child in cat.children:
                    blacklist.add(child)
                    blacklist_children(child)

        blacklist_children(category)
        return blacklist

    def create_category_from_form(category, form_data):
        """
        Create a new category based on the form data.
        """
        # Implement logic to create a category from the form data
        pass

    def update_category_from_form(category, category_id, form_data):
        """
        Update an existing category based on the form data.
        """
        # Implement logic to update a category from the form data
        pass

    def delete_category(category, category_id):
        """
        Delete a category.
        """
        # Implement logic to delete a category
        pass

    def get_category(category, category_id):
        """
        Retrieve a category from the database by its ID.
        """
        # Implement logic to retrieve a category by its ID from the database
        pass

    # Additional methods for database operations or form logic as needed
