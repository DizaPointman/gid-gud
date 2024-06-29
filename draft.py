"""
1. List Files and Folders
2. List affected Classes in File
3. Write Function Names
4. Add Input and Output to Functions
5. Write Functions
"""

# models.py
# Category Model
from sqlite3 import IntegrityError
from typing import Optional
from flask_login import current_user
from sqlalchemy import func, not_, update
from sqlalchemy.orm import validates
from app.models import Category, GidGud, User
from app.factory import db
from app.utils import exception_handler

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    parent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), index=True, nullable=True)
    parent: so.Mapped[Optional['Category']] = so.relationship('Category', remote_side=[id])
    path = db.Column(db.String(255), nullable=False, index=True)
    # real model has different syntax
    gidguds: so.Mapped[Optional[list['GidGud']]] = so.relationship('GidGud', back_populates='category')

    MAX_DEPTH = 5

    @validates('path')
    def validate_path(self, key, path):
        if not path or not all(part.isdigit() for part in path.split('.')):
            raise ValueError("Invalid path format: Path must be a dot-separated string of digits")
        return path

    @property
    def depth(self):
        return len(self.path.split('.'))

    def get_parent(self):
        return self.parent

    def get_children(self):
        return Category.query.filter(
            Category.path.like(f"{self.path}.%"),
            Category.depth == self.depth + 1
        ).all()
    def get_descendants(self):
        return Category.query.filter(Category.path.like(f"{self.path}.%")).all()

    def get_max_descendants_depth(self):
        max_depth = db.session.query(
            func.max(
                func.length(Category.path) - func.length(func.replace(Category.path, '.', '')) + 1
            )
        ).filter(Category.path.like(f"{self.path}.%")).scalar()
        return max_depth if max_depth else self.depth

    def get_subtree_depth(self):
        return self.get_max_descendants_depth() - self.depth + 1

    def is_descendant_of(self, other):
        return self.path.startswith(f"{other.path}.")

    def set_parent(self, new_parent):
        if new_parent and self.is_descendant_of(new_parent):
            raise ValueError("Cannot set a descendant as parent")
        if new_parent:
            self.parent = new_parent
            new_path = f"{new_parent.path}.{self.id}"
        else:
            new_path = str(self.id)

        old_path = self.path if self.path else None
        self.path = new_path

        if old_path:
            subtree_paths_updated = self._update_subtree_paths(old_path, new_path)
        return subtree_paths_updated

    @classmethod
    def move_subtree(cls, category_id, new_parent_id=None):
        category = cls.query.get(category_id)
        if not category:
            raise ValueError("Category not found")

        new_parent = cls.query.get(new_parent_id) if new_parent_id else None
        subtree_moved = category.set_parent(new_parent)
        db.session.commit()
        return subtree_moved

    def _update_subtree_paths(self, old_path, new_path):
        if old_path == new_path:
            return

        # Start a transaction
        try:
            with db.session.begin():
                # Update the paths of all descendants
                db.session.execute(
                    update(Category)
                    .where(Category.path.like(f"{old_path}.%"))
                    .values(
                        path=func.concat(
                            new_path,
                            func.substr(Category.path, func.length(old_path) + 1)
                        )
                    )
                )

                # Update the category's own path
                db.session.execute(
                    update(Category)
                    .where(Category.id == self.id)
                    .values(path=new_path)
                )

                db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Path update failed due to integrity constraint")
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Path update failed due to an unexpected error: {e}")

    @classmethod
    def rebuild_tree(cls):
        """Rebuild the entire tree structure."""
        with db.session.begin():
            # Reset all paths
            cls.query.update({cls.path: cls.id.cast(db.String)})

            # Get all categories
            categories = cls.query.order_by(cls.id).all()

            # Rebuild paths
            for category in categories:
                parent = category.get_parent()
                category.path = f"{parent.path}.{category.id}" if parent else str(category.id)

                db.session.add(category)

            db.session.commit()

# content_manger.py
class ContentManager:

## Category

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
        old_parent_id = cat.get_parent_id()
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
        if new_children_id and new_children_id != cat.id:
            children_reassigned = self.cat_reassign_children(cat, new_children_id)
        if new_gidguds_id and new_gidguds_id != cat.id:
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
            (func.length(Category.path) - func.length(func.replace(Category.path, '.'))) >= max_depth_children
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

# Changes
# remove set_parent from init and put into create
# add parent, parent_id attributes to allow for path reconstruction

## GidGud
### change name
### change category
### change recurrence
### complete
### Funcs: create(data), create_from_form(form), create_from_batch(form), update(data), complete

# routes.py
# /templates