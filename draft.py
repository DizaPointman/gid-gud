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

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    path = db.Column(db.String(255), nullable=False, index=True)

    MAX_DEPTH = 5

    @validates('path')
    def validate_path(self, key, path):
        if not path or not all(part.isdigit() for part in path.split('.')):
            raise ValueError("Invalid path format")
        return path

    def __init__(self, name, parent=None):
        self.name = name
        self.set_parent(parent)

    @property
    def depth(self):
        return len(self.path.split('.'))

    def get_parent(self):
        if '.' in self.path:
            parent_id = int(self.path.rsplit('.', 1)[0].split('.')[-1])
            return Category.query.get(parent_id)
        return None

    def get_parent_id(self):
        if '.' in self.path:
            parent_id = int(self.path.rsplit('.', 1)[0].split('.')[-1])
            return parent_id
        return None

    def get_children(self):
        return Category.query.filter(Category.path.like(f"{self.path}.%")).filter(Category.depth == self.depth + 1).all()

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
        if new_parent:
            if self.is_descendant_of(new_parent):
                raise ValueError("Cannot set a descendant as parent")
            new_path = f"{new_parent.path}.{self.id}"
        else:
            new_path = str(self.id)

        old_path = self.path  # Capture the old path before updating
        subtree_paths_updated = self._update_subtree_paths(old_path, new_path)
        return subtree_paths_updated

    @classmethod
    def move_subtree(cls, category_id, new_parent_id=None):
        category = cls.query.get(category_id)
        if not category:
            raise ValueError("Category not found")

        new_parent = cls.query.get(new_parent_id) if new_parent_id else None
        subtree_moved = category.set_parent(new_parent)
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
                if parent:
                    category.path = f"{parent.path}.{category.id}"
                    db.session.add(category)

            db.session.commit()

# content_manger.py
class ContentManager:

## Category

    def get_category_by_id(self, id) -> Category:
        cat = Category.query.filter_by(Category.id == id).first()
        return cat

    def cat_create(self, data: dict, user: Optional[User] = None) -> Category:
        user = user or current_user
        name = data.get('name', None)
        parent = data.get('parent', None)
        if not (name or parent or user):
            raise ValueError('Need name, parent and user to create category')
        else:
            new_cat = Category(name=name, user=user, parent=parent)
            db.session.add(new_cat)
            db.session.commit()
            return new_cat

    def cat_get_or_create(self, name: str, user: Optional[User] = None) -> Category:
        user = user or current_user
        if not name:
            cat = self.cat_get_or_create_root(user)
        else:
            cat = Category.query.get(Category).filter(Category.user == user, Category.name == 'name').first()
            if not cat:
                parent = self.cat_get_or_create_root(user)
                data = {'name': name, 'parent': parent}
                cat = self.cat_create(data, user)
        return cat

    def cat_get_or_create_root(self, user: Optional[User] = None) -> Category:
        user = user or current_user
        root = Category.query.get(Category).filter(Category.user == user, Category.name == 'root').first()
        if not root:
            root = Category(name='root', user=user, parent=None)
            db.session.add(root)
            db.session.commit()
        return root

    def cat_create_from_form(self, form_data: dict) -> Category:
        user = form_data.get('user', current_user)
        name = form_data.get('name', None)
        parent_id = form_data.get('parent', None)
        if parent_id:
            parent = self.get_category_by_id(parent)
        if not parent:
            parent = self.cat_get_or_create_root(user)
        data = {'name': name, 'parent': parent}
        new_cat = self.cat_create(data, user)
        return new_cat

    def cat_create_from_form_batch(self, form_data: dict) -> list[Category]:
        # Implement when time comes up
        return True

    def cat_update_from_form(self, cat: Category, form_data: dict) -> Category:
        # form validation checks for existing names
        old_name = cat.name
        new_name = form_data.get('name', None)
        old_parent_id = cat.get_parent_id()
        new_parent_id = form_data.get('parent', None)
        new_children_id = form_data.get('reassign_children', None)
        new_gidguds_id = form_data.get('reassign_gidguds', None)


        if new_name is not None and new_name != cat.name:
            name_updated = self.cat_update_name(cat, new_name)
        if new_parent_id is not None and new_parent_id != old_parent_id:
            parent_updated = self.cat_update_parent(cat, new_parent_id)
        if new_children_id is not None and new_children_id != cat.id:
            children_reassigned = self.cat_reassign_children(cat, new_children_id)
        if new_gidguds_id is not None and new_gidguds_id != cat.id:
            gidguds_reassigned = self.cat_reassign_gidguds(cat, new_gidguds_id)
        return True

    def cat_update_name(self, cat: Category, new_name: str) -> bool:
        cat.name = new_name
        db.session.commit()
        if cat.name == new_name:
            return True
        else:
            return False

    def cat_update_parent(self, cat: Category, new_parent_id: int) -> bool:
        new_parent = self.get_category_by_id(new_parent_id)
        if new_parent is not None:
            parent_changed = cat.set_parent(new_parent_id)
            return parent_changed
        else:
            return False

    def cat_reassign_children(self, cat: Category, new_parent_id: int) -> bool:
        children = cat.get_descendants()
        if children is not None:
            for child in children:
                child_reassigned = child.set_parent(new_parent_id)
                if not child_reassigned:
                    return False
            db.session.commit()
            return True
        return False

    def cat_reassign_gidguds(self, cat: Category, new_parent_id: int) -> bool:
        db.session.query(GidGud).filter(GidGud.category_id == cat.id).update({GidGud.category_id: new_parent_id}, synchronize_session=False)
        db.session.commit()
        return True

    def cat_archive_and_recreate(self, cat: Category) -> Category:
        return True

    def cat_get_possible_parents(self, cat: Category) -> dict[int, str]:
        max_d_parent = Category.MAX_DEPTH - cat.get_subtree_depth()
        return db.session.query(Category.id, Category.name).filter(
            Category.depth <= max_d_parent,
            ~Category.path.like(f"{cat.path}.%")
        ).all()

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
            not_(Category.id.in_(blacklist_ids))
        ).all()

    def cat_get_possible_parents_for_children(self, cat: Category) -> dict[int, str]:
        max_d_parent = Category.MAX_DEPTH - cat.get_subtree_depth() + 1

        possible_parents = db.session.query(Category.id, Category.name).filter(
            Category.depth <= max_d_parent,
            Category.id != cat.id,
            ~Category.path.like(f"{cat.path}.%")
        ).all()

        possible_parents.append((cat.id, cat.name))
        return possible_parents

## GidGud
### change name
### change category
### change recurrence
### complete
### Funcs: create(data), create_from_form(form), create_from_batch(form), update(data), complete

# routes.py
# /templates