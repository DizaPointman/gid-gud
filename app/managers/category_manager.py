

from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DatabaseError
from app.utils import log_exception
from app.models import Category
from app.factory import db

class CategoryManager:


    def __init__(self, db=None):

        self.db = db


    @staticmethod
    def return_or_create_category(name=None, user=None, parent=None):

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
                root = Category(name='root', user=user, depth=0, height=Category.MAX_HEIGHT)
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
                    parent.update_depth_and_height()
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

    def update_depth(self):
        if self.parent is not None:
            self.depth = self.parent.depth + 1
            if self.children:
                for child in self.children:
                    child.update_depth()

    def update_height(self):
        if self.parent is not None:
            if not self.children:
                self.height = 1
            else:
                self.height = max(child.height for child in self.children) + 1
                if self.parent.height != self.height + 1:
                    self.parent.update_height()

    def update_depth_and_height(self):

        if self.parent is not None:
            self.update_depth()
            self.update_height()

    def get_possible_children(self):

        # Generate blacklist because ancestors can't be children
        blacklist = self.generate_blacklist_ancestors()
        # Filter out blacklisted categories and those that would violate MAX_HEIGHT
        return [category for category in self.user.categories if category not in blacklist and self.depth + category.height <= self.MAX_HEIGHT] or []

    def generate_blacklist_ancestors(self):

        # Generate blacklist by adding self and recursively adding parents
        blacklist = set()
        category = self
        while category.parent:
            blacklist.add(category)
            category = category.parent
        blacklist.add(self)  # Add self to the blacklist
        return blacklist


    def get_possible_parents(self):

        # Generate blacklist because descendants can't be parents
        blacklist = self.generate_blacklist_descendants()
        # Filter out blacklisted categories and those that would violate MAX_HEIGHT
        return [category for category in self.user.categories if category not in blacklist and self.height + category.depth <= self.MAX_HEIGHT]

    def generate_blacklist_descendants(self):

        # Generate blacklist by adding self and recursively adding children
        blacklist = set()
        def blacklist_children(category):
            if category.children:
                for child in category.children:
                    blacklist.add(child)
                    blacklist_children(child)
        blacklist.add(self)  # Add self to the blacklist
        blacklist_children(self)
        return blacklist

    def create_category_from_form(self, form_data):
        """
        Create a new category based on the form data.
        """
        # Implement logic to create a category from the form data
        pass

    def update_category_from_form(self, category_id, form_data):
        """
        Update an existing category based on the form data.
        """
        # Implement logic to update a category from the form data
        pass

    def delete_category(self, category_id):
        """
        Delete a category.
        """
        # Implement logic to delete a category
        pass

    def get_category(self, category_id):
        """
        Retrieve a category from the database by its ID.
        """
        # Implement logic to retrieve a category by its ID from the database
        pass

    # Additional methods for database operations or form logic as needed
