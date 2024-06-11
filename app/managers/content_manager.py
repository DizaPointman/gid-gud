from datetime import datetime, timedelta
import inspect
from flask import current_app, flash
from flask_login import current_user
from pytz import utc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DatabaseError
import sqlalchemy as sa
from app.utils import handle_exception, log_exception
from app.models import Category, GidGud, User
from app.factory import db


class ContentManager:

    # Setting a maximum height for categories tree
    MAX_HEIGHT = Category.MAX_HEIGHT


    def __init__(self, db=None):

        self.db = db

    # Utilities
    def test_cm(self):
        print("c_man is alive")
        return current_app.logger.info("Testing category manager initialization")

    def iso_now(self):
        return datetime.now(utc).isoformat()

    def map_form_to_object_changes(obj, form):
        changes = {}

        # Iterate over the fields in the form
        for field_name, field_value in form.data.items():
            # Check if the field name corresponds to an attribute of the object
            if hasattr(obj, field_name):
                # Get the current value of the attribute
                current_value = getattr(obj, field_name)
                # Compare the form field value with the current attribute value
                if current_value != field_value:
                    # If they're different, add the change to the dictionary
                    changes[field_name] = field_value
            else:
                # Include additional parameters provided by form
                changes[field_name] = field_value

        return changes


    def get_user_by_id(self, id):
        # FIXME: implement this error handling for database critical functions
        try:
            user = User.query.filter_by(id=id).first()
            if user is None:
                raise ValueError(f"User with id {id} not found.")
            return user
        except SQLAlchemyError as e:
            handle_exception(e)
        except Exception as e:
            handle_exception(e)


    def get_category_by_id(self, id):
        return Category.query.filter_by(id=id).first()

    def get_category_by_name(self, name):
        return Category.query.filter_by(name=name).first()

    #TODO: change category functions to be based on id
    # user = self.get_user_by_id(user_id)

    def return_or_create_root_category(self, user):
        """
        Return or create the root category for the given user.
        """
        root = Category.query.filter_by(name='root', user_id=user.id).first()
        if not root:
            root = Category(name='root', user=user, depth=0, height=self.MAX_HEIGHT)
            db.session.add(root)
            db.session.commit()
        return root

    def return_or_create_root_category2(self, user_id):
        """
        Return or create the root category for the given user.
        """
        root = Category.query.filter_by(name='root', user_id=user_id).first()
        if not root:
            user = self.get_user_by_id(user_id)
            root = Category(name='root', user=user, depth=0, height=self.MAX_HEIGHT)
            db.session.add(root)
            db.session.commit()
        return root

    def create_category(self, name, user, parent):
        """
        Create a new category with the given name, user, and parent.
        """
        category = Category(name=name, user=user, parent=parent)
        db.session.add(category)
        self.update_depth_and_height(parent)
        db.session.commit()
        return category

    def create_category2(self, user_id, name, parent):
        """
        Create a new category with the given name, user, and parent.
        """
        user = self.get_user_by_id(user_id)
        category = Category(name=name, user=user, parent=parent)
        db.session.add(category)
        self.update_depth_and_height(parent)
        db.session.commit()
        return category

    def return_or_create_category(self, user=None, name=None, parent=None):
        """
        Return or create a category with the given name and user. If no name is provided, return the root category.
        """
        try:
            user = user or current_user

            if not user or not hasattr(user, 'id'):
                raise ValueError("A valid user must be provided")

            root = self.return_or_create_root_category(user)

            if not name:
                return root

            category = Category.query.filter_by(name=name, user_id=user.id).first()
            if not category:
                parent = parent or root
                category = self.create_category2(name, user, parent)

            return category

        except SQLAlchemyError as e:
            log_exception(e)
            db.session.rollback()
            return False
        except Exception as e:
            log_exception(e)
            db.session.rollback()
            return False

    def return_or_create_category2(self, user_id, name=None, parent=None):
        """
        Return or create a category with the given name and user. If no name is provided, return the root category.
        """
        try:
            user = self.get_user_by_id(user_id)

            root = self.return_or_create_root_category2(user_id)

            if not name:
                return root

            category = Category.query.filter_by(name=name, user_id=user_id).first()
            if not category:
                parent = parent or root
                category = self.create_category2(user.id, name, parent)

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
                    self.update_depth(child)

    def update_height(self, category):
        if category.parent is not None:
            if not category.children:
                category.height = 1
            else:
                category.height = max(child.height for child in category.children) + 1
                if category.parent.height != category.height + 1:
                    self.update_height(category.parent)

    def update_depth_and_height(self, *args):

        try:
            for category in args:

                if category.parent is not None:
                    self.update_depth(category)
                    self.update_height(category)

        except SQLAlchemyError as e:
            log_exception(e)
            db.session.rollback()
            return False
        except Exception as e:
            log_exception(e)
            db.session.rollback()
            return False

    def get_possible_children(self, category):
        # Return list of category names for potential children

        # Generate blacklist because ancestors can't be children
        blacklist = self.generate_blacklist_ancestors(category)
        # Filter out blacklisted categories and those that would violate MAX_HEIGHT
        return [cat.name for cat in category.user.categories if cat.name not in blacklist and category.depth + cat.height <= self.MAX_HEIGHT] or []

    def generate_blacklist_ancestors(self, category):

        # Generate blacklist by adding category and recursively adding parents
        blacklist = set()
        blacklist.add(category.name)  # Add the initial category
        while category.parent:
            category = category.parent
            blacklist.add(category.name)
        return blacklist

    def get_possible_parents(self, category):
        # Return list of category names for potential parents

        # Generate blacklist because descendants can't be parents
        blacklist = self.generate_blacklist_descendants(category)

        # Filter out blacklisted categories and those that would violate MAX_HEIGHT
        # Exclude and add root to install order
        return ['root'] + [cat.name for cat in category.user.categories if cat.name not in blacklist and category.height + cat.depth <= self.MAX_HEIGHT]

    def get_possible_parents_for_children(self, category):
        # Return list of category names for potential new parents for children

        if category.name == 'root':
            raise ValueError("You can't reassign all children of the root category at once!")

        if not category.children:
            return []
        else:
            max_height_children = max(child.height for child in category.children)
            blacklist = set()
            for child in category.children:
                temp_blacklist = self.generate_blacklist_descendants(child)
                blacklist.update(temp_blacklist)
            return ['root'] + [cat.name for cat in category.user.categories if cat.name not in blacklist and max_height_children + cat.depth <= self.MAX_HEIGHT]

    def generate_blacklist_descendants(self, category):

        # Generate blacklist by adding category and recursively adding children
        blacklist = set()
        blacklist.add(category.name)  # Add category to the blacklist
        blacklist.add('root')   # Remove root to later add in correct order

        def blacklist_children(cat):
            if cat.children:
                for child in cat.children:
                    blacklist.add(child.name)
                    blacklist_children(child)

        blacklist_children(category)
        return blacklist

    def update_category_from_form(self, category_id, form_data):
        """
        Update an existing category based on the form data.
        """
        try:

            category = self.get_category_by_id(category_id)
            old_name = category.name

            # Change parent category
            # TODO: update height depth for old and new parent
            if form_data.parent.data != category.parent.name:
                old_parent = category.parent
                new_parent = self.get_category_by_name(form_data.parent.data)
                category.parent = new_parent

                # Updating old parent and new parent to maintain tree structure
                self.update_depth_and_height(old_parent, new_parent)

                flash(f"Parent changed from <{old_parent.name}> to <{new_parent.name}>!")

            # Reassign GidGuds to new category
            if form_data.reassign_gidguds.data not in [old_name, 'No GidGuds']:
                relocate_gg = self.get_category_by_name(form_data.reassign_gidguds.data)
                db.session.query(GidGud).filter(GidGud.category_id == category_id).update(
                    {GidGud.category_id: relocate_gg.id}, synchronize_session=False)

                flash(f"GidGuds from <{old_name}> reassigned to <{relocate_gg.name}>!")

            # Reassign child categories
            if form_data.reassign_children.data not in [old_name, 'No Children']:
                relocate_cc = self.get_category_by_name(form_data.reassign_children.data)
                db.session.query(Category).filter(Category.parent_id == category_id).update(
                    {Category.parent_id: relocate_cc.id}, synchronize_session=False)

                # Updating the category and new parent to maintain tree structure
                self.update_depth_and_height(category, relocate_cc)

                flash(f"Child categories from <{old_name}> reassigned to <{relocate_cc.name}>!")

            # Rename the category
            if form_data.name.data != old_name:
                new_name = form_data.name.data
                category.name = new_name

                flash(f"Name changed from <{old_name}> to <{new_name}>!")

            # Commit the transaction
            db.session.commit()

            return True

        except SQLAlchemyError as e:
            log_exception(e)
            db.session.rollback()
            return False
        except Exception as e:
            log_exception(e)
            db.session.rollback()
            return False

    def delete_category(self, category_id):
        """
        Delete a category.
        """
        # Implement logic to delete a category
        pass

    # GidGud

    def get_gidgud_by_id(self, id):
        try:
            gg = GidGud.query.filter_by(id=id).first()
            if gg is None:
                raise ValueError(f"GidGud with id {id} not found.")
            return gg
        except SQLAlchemyError as e:
            handle_exception(e)
        except Exception as e:
            handle_exception(e)

    def gidgud_handle_update(self, gidgud, form):

        # TODO: if gidgud.completed_at is not None, create a new gidgud and return it, archive old gidgud
        # TODO: only create new when body, category, unit or times is changed, not on rec rhythm change
        # TODO: make sure data from edit is correctly applied if rec_val and/or rec_unit is missing (None)

        try:
            if gidgud.completed_at is None:

                gidgud.body = form.body.data
                if form.category.data is not gidgud.category.name:
                    updated_category = self.return_or_create_category(name=(form.category.data))
                    gidgud.category = updated_category
                if form.rec_instant.data:
                    gidgud.rec_val = 1
                    gidgud.rec_unit = 'instantly'
                if form.rec_val.data is not None:
                    if form.rec_val.data is not gidgud.rec_val:
                        gidgud.rec_val = form.rec_val.data
                        if gidgud.rec_next is not None:
                            gidgud.rec_next = None
                if form.rec_unit.data is not None:
                    if form.rec_unit.data is not gidgud.rec_unit:
                        gidgud.rec_unit = form.rec_unit.data
                        if gidgud.rec_next is not None:
                            gidgud.rec_next = None

                db.session.commit()

                return True

            else:

                # Archive old GidGud
                gidgud.archived_at = True
                # Create new GidGud
                body = form.body.data or gidgud.body
                category = self.return_or_create_category(name=(form.category.data)) or gidgud.category
                rec_val = form.rec_val.data or gidgud.rec_val
                rec_unit = form.rec_unit.data or gidgud.rec_unit

                gid = GidGud(body=body, user_id=current_user.id, category=category, rec_val=rec_val, rec_unit=rec_unit)
                db.session.add(gid)
                db.session.commit()

                return True

        except Exception as e:
            # Log any exceptions that occur during the process
            log_exception(e)
            return False

    def gidgud_handle_complete(self, gidgud):
        # TODO: also archive?
        try:
            timestamp = self.iso_now()

            if gidgud.completed_at is not None:
                gidgud.completed_at.append(timestamp)
            else:
                gidgud.completed_at = timestamp

            if gidgud.rec_val != 0:

                if gidgud.rec_val == 1 and gidgud.rec_unit == 'instantly':
                    rec_next = timestamp
                else:
                    delta = timedelta(**{gidgud.rec_unit: gidgud.rec_val})
                    rec_next = (datetime.fromisoformat(timestamp) + delta).isoformat()

                gidgud.rec_next = rec_next

            db.session.commit()
            return True

        except Exception as e:
            # Log any exceptions that occur during the process
            log_exception(e)
            return False

    def gidgud_create_from_form(self, user_id, form):

        user = self.get_user_by_id(user_id)
        category = self.return_or_create_category2(user_id, form.category.data)
        rec_val, rec_unit, rec_next = GidGud.set_rec(reset_timer=True, rec_instant=form.rec_instant.data, rec_custom=form.rec_custom.data)
        gg = GidGud.create(body=form.body.data, user=user, category=category, rec_val=rec_val, rec_unit=rec_unit, rec_next=rec_next)

        return gg

    def gidgud_update_from_form(self, gidgud_id, user_id, form):

        gg = self.get_gidgud_from_id(gidgud_id)
        changes = self.map_form_to_object_changes(gg, form)
        changes['rec_val'], changes['rec_unit'], changes['rec_next'] = gg.set_rec(**changes)

        if 'category' in changes:
            changes['category'] = self.return_or_create_category2(user_id, form.category.data)

        gg.update_gidgud(**changes)

        return gg

    def gidgud_handle_complete2(self, id):

        timestamp = datetime.now(utc)
        gg = GidGud.query.filter_by(id=id).first()
        custom_data = None

        gg.add_completion_entry(timestamp, custom_data)
        rec_next = gg.update_rec_next(timestamp)
        if not rec_next: gg.archived_at_datetime(timestamp)
        gg.modified_at_datetime(timestamp)

        db.session.commit()
        return rec_next


    def gidgud_return_dict_from_choice(self, choice):

        choices = ['gids', 'guds', 'sleep', 'all']
        gidgud_dict = {}

        try:
            if 'all' in choice:
                gidguds = db.session.execute(sa.select(GidGud).where(current_user == GidGud.author)).scalars().all()
                gidgud_dict['all'] = gidguds

            if 'guds' in choice:
                guds = db.session.execute(
                    sa.select(GidGud)
                    .where((current_user == GidGud.author) & (GidGud.completed_at.isnot(None)))
                ).scalars().all()
                gidgud_dict['guds'] = guds

            if 'gids' in choice or 'sleep' in choice:
                gids_and_sleep = db.session.scalars(
                    sa.select(GidGud)
                    .where((current_user == GidGud.author) & (GidGud.completed_at.is_(None)))
                )
                gids = []
                sleep = []

                for gidgud in gids_and_sleep:
                    if 'gids' in choice:
                        if not gidgud.rec_next or (self.check_sleep(gidgud) <= 0):
                            gids.append(gidgud)
                    if 'sleep' in choice:
                        if gidgud.rec_next and self.check_sleep(gidgud) > 0:
                            sleep.append(gidgud)

                if 'gids' in choice:
                    gidgud_dict['gids'] = gids
                if 'sleep' in choice:
                    gidgud_dict['sleep'] = sleep

            return gidgud_dict

        except Exception as e:
            # Log any exceptions that occur during the process
            log_exception(e)
            return False

    def check_sleep(self, gidgud):
        datetime_now = datetime.fromisoformat(self.iso_now())
        gidgud_rec_next = datetime.fromisoformat(gidgud.rec_next)
        sleep = (gidgud_rec_next - datetime_now).total_seconds()
        return sleep

    def gidgud_return_dict_from_choice2(self, choice):

            choices = ['gids', 'guds', 'sleep', 'all']
            gidgud_dict = {}
            gidguds = db.session.execute(sa.select(GidGud).where(current_user == GidGud.author)).scalars().all()

            try:
                if 'all' in choice:
                    gidguds = db.session.execute(sa.select(GidGud).where(current_user == GidGud.author)).scalars().all()
                    gidgud_dict['all'] = gidguds

                if 'guds' in choice:
                    guds = db.session.execute(
                        sa.select(GidGud)
                        .where((current_user == GidGud.author) & (GidGud.completed_at.isnot(None)))
                    ).scalars().all()
                    gidgud_dict['guds'] = guds

                if 'gids' in choice or 'sleep' in choice:
                    gids_and_sleep = db.session.scalars(
                        sa.select(GidGud)
                        .where((current_user == GidGud.author) & (GidGud.completed_at.is_(None)))
                    )
                    gids = []
                    sleep = []

                    for gidgud in gids_and_sleep:
                        if 'gids' in choice:
                            if not gidgud.rec_next or (self.check_sleep(gidgud) <= 0):
                                gids.append(gidgud)
                        if 'sleep' in choice:
                            if gidgud.rec_next and self.check_sleep(gidgud) > 0:
                                sleep.append(gidgud)

                    if 'gids' in choice:
                        gidgud_dict['gids'] = gids
                    if 'sleep' in choice:
                        gidgud_dict['sleep'] = sleep

                return gidgud_dict

            except Exception as e:
                # Log any exceptions that occur during the process
                log_exception(e)
                return False