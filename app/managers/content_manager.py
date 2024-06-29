from datetime import datetime, timedelta
import inspect
from typing import Optional
from flask import current_app, flash
from flask_login import current_user
from pytz import utc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, ProgrammingError, DatabaseError
import sqlalchemy as sa
from app.utils import exception_handler, handle_exception, log_exception
from app.models import Category, CompletionTable, GidGud, User
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

    @exception_handler
    def get_category_by_id(self, id) -> Optional[Category]:
        return Category.query.filter_by(id=id).first()

    @exception_handler
    def cat_create(self, data: dict, user: Optional[User] = None) -> Category:
        user = user or current_user
        name = data.get('name')
        parent = data.get('parent')
        if not (name or parent or user):
            raise ValueError('Need name, parent, and user to create category')
        new_cat = Category(name=name)
        db.session.add(new_cat)
        db.session.commit()
        new_cat.set_parent(parent)
        return new_cat

    @exception_handler
    def cat_get_or_create(self, name: str, user: Optional[User] = None) -> Category:
        user = user or current_user
        if not name:
            return self.cat_get_or_create_root(user)
        cat = Category.query.filter_by(user=user, name=name).first()
        if not cat:
            parent = self.cat_get_or_create_root(user)
            data = {'name': name, 'parent': parent}
            cat = self.cat_create(data, user)
        return cat

    @exception_handler
    def cat_get_or_create_root(self, user: Optional[User] = None) -> Category:
        user = user or current_user
        root = Category.query.filter_by(user=user, name='root').first()
        if not root:
            root = Category(name='root', parent=None)
            db.session.add(root)
            db.session.commit()
        return root

    @exception_handler
    def cat_create_from_form(self, form_data: dict) -> Category:
        user = form_data.get('user', current_user)
        name = form_data.get('name')
        parent_id = form_data.get('parent')
        parent = self.get_category_by_id(parent_id) if parent_id else self.cat_get_or_create_root(user)

        data = {'name': name, 'parent': parent}
        return self.cat_create(data, user)

    @exception_handler
    def cat_create_from_form_batch(self, form_data: dict) -> list[Category]:
        # Implement when time comes up
        return []

    @exception_handler
    def cat_update_from_form(self, cat: Category, form_data: dict) -> bool:
        old_name = cat.name
        new_name = form_data.get('name')
        old_parent_id = cat.parent_id
        new_parent_id = form_data.get('parent')
        new_children_id = form_data.get('reassign_children')
        new_gidguds_id = form_data.get('reassign_gidguds')

        name_updated = True
        parent_updated = True
        children_reassigned = True
        gidguds_reassigned = True

        if new_name and new_name != old_name:
            name_updated = self.cat_update_name(cat, new_name)
        if new_parent_id and new_parent_id != old_parent_id:
            parent_updated = self.cat_update_parent(cat, new_parent_id)
        if new_children_id and new_children_id != (cat.id or 'No Children'):
            children_reassigned = self.cat_reassign_children(cat, new_children_id)
        if new_gidguds_id and new_gidguds_id != (cat.id or 'No GidGuds'):
            gidguds_reassigned = self.cat_reassign_gidguds(cat, new_gidguds_id)

        return name_updated and parent_updated and children_reassigned and gidguds_reassigned

    @exception_handler
    def cat_update_name(self, cat: Category, new_name: str) -> bool:
        cat.name = new_name
        db.session.commit()
        return cat.name == new_name

    @exception_handler
    def cat_update_parent(self, cat: Category, new_parent_id: int) -> bool:
        new_parent = self.get_category_by_id(new_parent_id)
        if new_parent:
            parent_changed = cat.set_parent(new_parent)
            db.session.commit()
            return parent_changed
        return False

    @exception_handler
    def cat_reassign_children(self, cat: Category, new_parent_id: int) -> bool:
        new_parent = self.get_category_by_id(new_parent_id)  # Retrieve the new_parent object
        children = cat.get_descendants()
        if children:
            for child in children:
                child_reassigned = child.set_parent(new_parent_id)
                if not child_reassigned:
                    return False
            db.session.commit()
            return True
        return False

    @exception_handler
    def cat_reassign_gidguds(self, cat: Category, new_parent_id: int) -> bool:
        db.session.query(GidGud).filter_by(category_id=cat.id).update({GidGud.category_id: new_parent_id}, synchronize_session=False)
        db.session.commit()
        return True

    @exception_handler
    def cat_archive_and_recreate(self, cat: Category) -> Category:
        # Implement when time comes up
        return True

    @exception_handler
    def cat_get_possible_parents(self, cat: Category) -> dict[int, str]:
        max_d_parent = Category.MAX_DEPTH - cat.get_subtree_depth()
        return db.session.query(Category.id, Category.name).filter(
            Category.depth <= max_d_parent,
            ~Category.path.like(f"{cat.path}.%")
        ).all()

    @exception_handler
    def cat_get_possible_children(self, cat: Category) -> dict[int, str]:
        max_depth_children = Category.MAX_DEPTH - cat.depth
        if max_depth_children <= 0:
            return []

        blacklist_paths = set(path[0] for path in db.session.query(Category.path).filter(
            (sa.func.length(Category.path) - sa.func.length(sa.func.replace(Category.path, '.'))) >= max_depth_children
        ).all()) | {cat.path}

        blacklist_ids = {
            int(id)
            for path in blacklist_paths
            for id in path.split('.')[:-max_depth_children]
        }

        return db.session.query(Category.id, Category.name).filter(
            ~Category.id.in_(blacklist_ids)
        ).all()

    @exception_handler
    def cat_get_possible_parents_for_children(self, cat: Category) -> dict[int, str]:
        max_d_parent = Category.MAX_DEPTH - cat.get_subtree_depth() + 1

        possible_parents = db.session.query(Category.id, Category.name).filter(
            Category.depth <= max_d_parent,
            Category.id != cat.id,
            ~Category.path.like(f"{cat.path}.%")
        ).all()

        possible_parents.append((cat.id, cat.name))
        return possible_parents

    @exception_handler
    def cat_get_all_id_name(self):
        return db.session.query(Category.id, Category.name).all()

    def delete_category(self, category_id):
        """
        Delete a category.
        """
        # Implement logic to delete a category
        pass

    # GidGud

    def get_gidgud_by_id(self, id) -> Optional[GidGud]:
        try:
            gg = GidGud.query.filter_by(id=id).first()
            if gg is None:
                current_app.logger.warning(f"GidGud with id {id} not found.")
                return None
            return gg
        except SQLAlchemyError as e:
            handle_exception(e)
            return None

    def gidgud_handle_update(self, gidgud, form):

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

    def gidgud_create_from_form(self, user, form):
        """
        Creates a GidGud instance from a form.

        :param form: The form containing the data for creating the GidGud instance.
        :param user: The user associated with the GidGud instance. Defaults to current_user.
        :return: The created GidGud instance.
        """

        body = form.body.data
        category = self.return_or_create_category(user, form.category.data)

        reset_timer = form.reset_timer.data or False
        rec_instant = form.rec_instant.data
        rec_custom = form.rec_custom.data
        rec_next = form.rec_next.data.isoformat() or self.iso_now()

        if not rec_instant and not rec_custom:
            rec = False
            rec_val = 0
            rec_unit = 'days'

        elif rec_instant:
            rec = True
            rec_val = 0
            rec_unit = 'days'

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
        arch_and_recr = False

        user = gg.user
        body = form.body.data
        category = self.return_or_create_category(form.category.data)

        reset_timer = form.reset_timer.data
        rec_instant = form.rec_instant.data
        rec_custom = form.rec_custom.data
        rec_next = gg.rec_next or form.rec_next.data.isoformat()

        if reset_timer:
            gg.rec_next = self.iso_now()

        # Handle body change and archiving
        if body != gg.body:
            if arch_and_recr:
                gg = self.archive_and_recreate_gidgud(gg, form, user)
            else:
                gg.body = form.body.data

        if not rec_instant and not rec_custom:
            gg.rec = False
            gg.rec_val = 0
            gg.rec_unit = 'days'

        elif rec_instant:
            gg.rec = True
            gg.rec_val = 0
            gg.rec_unit = 'days'

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
        if rec_next is None:
            gg.archived_at_datetime = timestamp
            gg.rec_val = None
            gg.rec_unit = None
        gg.modified_at_datetime = timestamp

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

    def get_active_gidguds(self, user):

        now = datetime.now(utc).isoformat()

        gidguds = db.session.execute(
            sa.select(GidGud).where(
                (GidGud.author == user) &
                (GidGud.archived_at == None) &
                ((GidGud.rec_next == None) | (GidGud.rec_next <= now))
            ).order_by(GidGud.created_at.desc())
        ).scalars()
        return gidguds

    def get_inactive_gidguds(self, user):

        now = datetime.now(utc).isoformat()

        gidguds = db.session.execute(
            sa.select(GidGud).where(
                (GidGud.author == user) &
                (GidGud.archived_at == None) &
                ((GidGud.rec_next == None) | (GidGud.rec_next >= now))
            ).order_by(GidGud.created_at.desc())
        ).scalars()
        return gidguds

    def get_completed_gidguds(self, user):
        # FIXME: redundant, already in models.py

        completions = db.session.scalars(sa.select(CompletionTable).where(CompletionTable.user_id == user.id).order_by(CompletionTable.completed_at.desc()))
        return completions