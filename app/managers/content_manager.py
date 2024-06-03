from datetime import datetime, timedelta
from flask import current_app, flash
from flask_login import current_user
from pytz import utc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DatabaseError
import sqlalchemy as sa
from app.utils import log_exception
from app.models import Category, GidGud
from app.factory import db


class ContentManager:

    # Setting a maximum height for categories tree
    MAX_HEIGHT = Category.MAX_HEIGHT


    def __init__(self, db=None):

        self.db = db

    def test_cm(self):
        print("c_man is alive")
        return current_app.logger.info("Testing category manager initialization")

    def iso_now(self):
        return datetime.now(utc).isoformat()

    def get_category_by_id(self, category_id):
        return Category.query.filter_by(id=category_id).first()

    def get_category_by_name(self, category_name):
        return Category.query.filter_by(name=category_name).first()

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

    def create_category(self, name, user, parent):
        """
        Create a new category with the given name, user, and parent.
        """
        category = Category(name=name, user=user, parent=parent)
        db.session.add(category)
        self.update_depth_and_height(parent)
        db.session.commit()
        return category

    def return_or_create_category(self, name=None, user=None, parent=None):
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
                category = self.create_category(name, user, parent)

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

    def gidgud_handle_update(self, gidgud, form):

        # TODO: if gidgud.completed is not None, create a new gidgud and return it, archive old gidgud

        try:
            if gidgud.completed is None:

                gidgud.body = form.body.data
                if form.category.data is not gidgud.category.name:
                    updated_category = self.return_or_create_category(name=(form.category.data))
                    gidgud.category = updated_category
                if form.rec_rhythm.data is not gidgud.recurrence_rhythm:
                    gidgud.recurrence_rhythm = form.rec_rhythm.data
                    if gidgud.next_occurrence is not None:
                        gidgud.next_occurrence = None
                if form.time_unit.data is not gidgud.time_unit:
                    gidgud.time_unit = form.time_unit.data
                    if gidgud.next_occurrence is not None:
                        gidgud.next_occurrence = None

                db.session.commit()

                return True

            else:

                # Archive old GidGud
                gidgud.archived = True
                # Create new GidGud
                body = form.body.data or gidgud.body
                category = self.return_or_create_category(name=(form.category.data)) or gidgud.category
                recurrence_rhythm=form.rec_rhythm.data or gidgud.recurrence_rhythm
                time_unit = form.time_unit.data or gidgud.time_unit

                gid = GidGud(body=body, user_id=current_user.id, category=category, recurrence_rhythm=recurrence_rhythm, time_unit=time_unit)
                db.session.add(gid)
                db.session.commit()

                return True

        except Exception as e:
            # Log any exceptions that occur during the process
            log_exception(e)
            return False

    def gidgud_handle_complete(self, gidgud):
        try:
            timestamp = self.iso_now()

            if gidgud.completed is not None:
                gidgud.completed.append(timestamp)
            else:
                gidgud.completed = timestamp

            if gidgud.recurrence_rhythm != 0:

                if gidgud.recurrence_rhythm == 1 and gidgud.time_unit == 'None':
                    next_occurrence = timestamp
                else:
                    delta = timedelta(**{gidgud.time_unit: gidgud.recurrence_rhythm})
                    next_occurrence = (datetime.fromisoformat(timestamp) + delta).isoformat()

                gidgud.next_occurrence = next_occurrence

            db.session.commit()
            return True

        except Exception as e:
            # Log any exceptions that occur during the process
            log_exception(e)
            return False

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
                    .where((current_user == GidGud.author) & (GidGud.completed.isnot(None)))
                ).scalars().all()
                gidgud_dict['guds'] = guds

            if 'gids' in choice or 'sleep' in choice:
                gids_and_sleep = db.session.scalars(
                    sa.select(GidGud)
                    .where((current_user == GidGud.author) & (GidGud.completed.is_(None)))
                )
                gids = []
                sleep = []

                for gidgud in gids_and_sleep:
                    if 'gids' in choice:
                        if not gidgud.next_occurrence or (self.check_sleep(gidgud) <= 0):
                            gids.append(gidgud)
                    if 'sleep' in choice:
                        if gidgud.next_occurrence and self.check_sleep(gidgud) > 0:
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
        gidgud_next_occurrence = datetime.fromisoformat(gidgud.next_occurrence)
        sleep = (gidgud_next_occurrence - datetime_now).total_seconds()
        return sleep
    
    def gidgud_return_dict_from_choice2(self, user):

        print("GIDGUD return dict from choice")
        user = user or current_user
        gidguds = db.session.execute(sa.select(GidGud).where(user == GidGud.author)).scalars().all()
        gidgud_dict = {}

        try:
            # guds: every completed date is a gud
            # gids: completed is None or recurrence enabled while next occurrence is enabled
            # sleep: completed is None or recurrence enabled but next occurrence outstanding

            for g in gidguds:
                print(f"loop check outer: id: {g.id}, body: {g.body}")
                for c in g.completed:
                    print(f"loop check completed: id: {g.id}, body: {g.body}, date: {c}")
                    gidgud_dict['guds'] = {'body': g.body, 'date_completed': datetime.fromisoformat(c)}
                if g.completed is None and g.recurrence_rhythm == 0:
                    print(f"loop check rec 0, comp None: id: {g.id}, body: {g.body}")
                    gidgud_dict['gids'] = {'body': g.body, 'date_created': datetime.fromisoformat(g.timestamp)}
                if g.recurrence_rhythm != 0:
                    print(f"loop check rec not 0: id: {g.id}, body: {g.body}")
                    if not g.next_occurrence:
                        gidgud_dict['gids'] = {'body': g.body, 'date_created': datetime.fromisoformat(g.timestamp)}
                    else:
                        if self.check_sleep(g) <= 0:
                            gidgud_dict['gids'] = {'body': g.body, 'date_created': datetime.fromisoformat(g.timestamp)}
                        else:
                            gidgud_dict['sleep'] = {'body': g.body, 'date_created': datetime.fromisoformat(g.timestamp)}

            return gidgud_dict

        except Exception as e:
            # Log any exceptions that occur during the process
            log_exception(e)
            return False
