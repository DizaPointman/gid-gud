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

    def populate_form(form, data_source, fields):
        for field in fields:
            if hasattr(form, field) and hasattr(data_source, field):
                getattr(form, field).data = getattr(data_source, field)
            elif hasattr(form, field) and field in data_source:
                getattr(form, field).data = data_source[field]

        # Additional logic for rec_val and rec_unit based on rec_instant and rec_custom
        if 'rec_instant' in data_source and 'rec_custom' in data_source:
            rec_instant = data_source['rec_instant']
            rec_custom = data_source['rec_custom']

            if not rec_instant and not rec_custom:
                form.rec_val.data = 0
                form.rec_unit.data = 'No Rep'
            elif rec_instant and not rec_custom:
                form.rec_val.data = 0
                form.rec_unit.data = 'daily'
            elif rec_custom and not rec_instant:
                if 'rec_val' in data_source:
                    form.rec_val.data = data_source['rec_val']
                if 'rec_unit' in data_source:
                    form.rec_unit.data = data_source['rec_unit']

    def map_form_to_dict(self, form):
        form_dict = {field_name: field_value for field_name, field_value in form.data.items()}
        return form_dict

    def get_user_by_id(self, id) -> User:
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

    def get_category_by_id(self, id) -> Category:
        return Category.query.filter_by(id=id).first()

    def get_category_by_name(self, name) -> Category:
        user = current_user
        return Category.query.filter_by(name=name, user=user).first()

    def return_or_create_root_category(self, user=None):
        """
        Return or create the root category for the given user.
        """
        user = user or current_user
        root = Category.query.filter_by(name='root', user=user).first()
        if not root:
            root = Category(name='root', user=user, depth=0, height=self.MAX_HEIGHT)
            db.session.add(root)
            db.session.commit()
        return root

    def create_category(self, **kwargs):
        """
        Create a new category with the given name, user, and parent.
        """
        user = user or current_user
        parent = parent or self.return_or_create_root_category(user)
        category = Category(**kwargs)
        db.session.add(category)
        parents_updated = self.update_depth_and_height(parent)
        db.session.commit()
        return category

    def return_or_create_category(self, name=None, parent=None):
        """
        Return or create a category with the given name and user. If no name is provided, return the root category.
        """
        try:
            user = user or current_user

            root = self.return_or_create_root_category(user)

            if not name:
                return root

            category = Category.query.filter_by(name=name, user=user).first()
            if not category:
                parent = parent or root
                category = self.create_category(user=user, name=name, parent=parent)

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

    def get_possible_children(self, category):

        blacklist = self.generate_blacklist_ancestors(category)
        # Filter out blacklisted categories, those that would violate MAX_HEIGHT and archived categories
        is_valid_category = lambda cat: not cat.archived_at and cat.name not in blacklist and category.depth + cat.height <= self.MAX_HEIGHT

        return [cat.name for cat in category.user.categories if is_valid_category(cat)] or []

    def generate_blacklist_ancestors(self, category):

        # Generate blacklist by adding category and recursively adding parents
        blacklist = set()
        blacklist.add(category.name)  # Add the initial category
        while category.parent:
            category = category.parent
            blacklist.add(category.name)
        return blacklist

    def get_possible_parents(self, category):

        blacklist = self.generate_blacklist_descendants(category)
        # Filter out blacklisted categories, those that would violate MAX_HEIGHT and archived categories
        is_valid_category = lambda cat: cat.name not in blacklist and category.height + cat.depth <= self.MAX_HEIGHT and not cat.archived_at

        return ['root'] + [cat.name for cat in category.user.categories if is_valid_category(cat)]

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
            # Filter out blacklisted categories, those that would violate MAX_HEIGHT and archived categories
            is_valid_category_with_max_height = lambda cat: cat.name not in blacklist and max_height_children + cat.depth <= self.MAX_HEIGHT and not cat.archived_at

            return ['root'] + [cat.name for cat in category.user.categories if is_valid_category_with_max_height(cat)]

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

    def reassign_children_to_category(self, old_category, new_category):
        try:
            db.session.query(Category).filter(Category.parent_id == old_category.id).update({Category.parent_id: new_category.id}, synchronize_session=False)
            db.session.commit()
            parent_changed = self.update_depth_and_height(old_category, new_category)
            db.session.commit()
            return parent_changed
        except SQLAlchemyError as e:
            handle_exception(e)
            db.session.rollback()
            return None
        except Exception as e:
            handle_exception(e)
            db.session.rollback()
            return None

    def reassign_gidguds_to_category(self, old_category, new_category):
        try:
            db.session.query(GidGud).filter(GidGud.category_id == old_category.id).update({GidGud.category_id: new_category.id}, synchronize_session=False)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            handle_exception(e)
            db.session.rollback()
            return None
        except Exception as e:
            handle_exception(e)
            db.session.rollback()
            return None

    def archive_and_recreate_category(self, old_cat: Category, form):
        """
        Archive the old Category and create a new one with updated data.
        """
        try:
            name = form.name.data
            new_cat = self.create_category(name=name)

            is_archived = old_cat.archive_and_historize(new_cat)
            cc_reassigned = self.reassign_children_to_category(old_cat, new_cat)

            if is_archived and cc_reassigned:
                return new_cat
            else:
                raise ValueError("A problem occurred when archiving the old category.")

        except SQLAlchemyError as e:
            handle_exception(e)
            db.session.rollback()
            return None
        except Exception as e:
            handle_exception(e)
            db.session.rollback()
            return None

    def create_category_from_form(self, form):
        user = user or current_user
        name = form.name.data
        new_cat = Category(user=user, name=name)
        db.session.add(new_cat)
        db.session.commit()
        return new_cat

    def update_category_from_form(self, id, form):
        """
        Update an existing category based on the form data.
        """

        # TODO: new_cc = cc.archive_and_recreate(self, changes)
        # FIXME: Make this as beautiful as everything I built the last 48h

        try:

            cat = self.get_category_by_id(id)
            old_name = cat.name

            if cat.name != form.name.data:
                new_cat = self.archive_and_recreate_category(cat, form)
                cat = new_cat

            # Change parent category
            if form.parent.data != cat.parent.name:
                old_parent = cat.parent
                new_parent = self.get_category_by_name(form.parent.data)
                cat.parent = new_parent

                # Updating old parent and new parent to maintain tree structure
                parent_updated = self.update_depth_and_height(old_parent, new_parent)

                flash(f"Parent changed from <{old_parent.name}> to <{new_parent.name}>!")

            # Reassign GidGuds to new category
            if form.reassign_gidguds.data not in [cat.name, 'No GidGuds']:
                reas_gg = self.get_category_by_name(form.reassign_gidguds.data)
                gg_reassigned = self.reassign_gidguds_to_category(cat, reas_gg)

                flash(f"GidGuds from <{old_name}> reassigned to <{reas_gg.name}>!")

            # Reassign child categories
            if form.reassign_children.data in [cat.name, 'No Children']:
                reas_cc = self.get_category_by_name(form.reassign_children.data)
                cc_reassigned = self.reassign_children_to_category(cat, reas_cc)

                flash(f"Child categories from <{old_name}> reassigned to <{reas_cc.name}>!")


            # Commit the transaction
            db.session.commit()

            return cat

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

    def get_gidgud_by_id(self, id) -> GidGud:
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

    def gidgud_create_from_form(self, form, user=None):
        """
        Creates a GidGud instance from a form.

        :param form: The form containing the data for creating the GidGud instance.
        :param user: The user associated with the GidGud instance. Defaults to current_user.
        :return: The created GidGud instance.
        """
        user = user or current_user
        body = form.body.data
        category = self.return_or_create_category(form.category.data)

        reset_timer = form.reset_timer.data or False
        rec_instant = form.rec_instant.data
        rec_custom = form.rec_custom.data
        # TODO: check that data is datetime object
        rec_next = form.rec_next.data or self.iso_now()

        if not rec_instant and not rec_custom:
            rec = False
            rec_val = 0
            rec_unit = 'daily'

        elif rec_instant:
            rec = True
            rec_val = 0
            rec_unit = 'daily'

        elif rec_custom:
            rec = True
            rec_val = form.rec_val.data
            rec_unit = form.rec_unit.data

        gg = GidGud(author=user, body=body, category=category, rec=rec, rec_val=rec_val, rec_unit=rec_unit, rec_next=rec_next)
        db.session.add(gg)
        db.session.commit()

        return gg

    def gidgud_update_from_form(self, id, form):
        """
        Updates a GidGud instance from a form.

        :param id: The ID of the GidGud instance to update.
        :param form: The form containing the updated data.
        :return: The updated GidGud instance.
        """
        gg = self.get_gidgud_by_id(id)
        user = gg.user
        body = form.body.data
        category = self.return_or_create_category(form.category.data)

        reset_timer = form.reset_timer.data
        rec_instant = form.rec_instant.data
        rec_custom = form.rec_custom.data
        rec_next = gg.rec_next or form.rec_next.data

        if reset_timer:
            gg.rec_next = self.iso_now()

        # Handle body change and archiving
        if body != gg.body:
            gg = self.archive_and_recreate_gidgud(gg, form, user)
        else:
            if not rec_instant and not rec_custom:
                gg.rec = False
                gg.rec_val = 0
                gg.rec_unit = 'daily'

            elif rec_instant:
                gg.rec = True
                gg.rec_val = 0
                gg.rec_unit = 'daily'

            elif rec_custom:
                gg.rec = True
                gg.rec_val = form.rec_val.data
                gg.rec_unit = form.rec_unit.data
            gg.category = category
            gg.rec_next = rec_next

        db.session.commit()

        return gg

    def gidgud_handle_complete(self, id):

        timestamp = datetime.now(utc)
        gg = self.get_gidgud_by_id(id)
        custom_data = None

        gg.add_completion_entry(timestamp, custom_data)
        rec_next = gg.update_rec_next(timestamp)
        if not rec_next: gg.archived_at_datetime(timestamp)
        gg.modified_at_datetime(timestamp)

        db.session.commit()
        return rec_next

    def archive_and_recreate_gidgud(self, gg: GidGud, form, user):
        """
        Archive the old GidGud and create a new one with updated data.
        """
        try:
            new_gg = self.gidgud_create_from_form(form, user)
            is_archived = gg.archive_and_historize(new_gg)
            if is_archived:
                return new_gg

        except SQLAlchemyError as e:
            handle_exception(e)
            db.session.rollback()
            return None
        except Exception as e:
            handle_exception(e)
            db.session.rollback()
            return None


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