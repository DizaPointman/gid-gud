

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
