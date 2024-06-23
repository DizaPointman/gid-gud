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
from sqlalchemy import and_, func, not_, or_, union, update
from sqlalchemy.orm import validates
from app.models import Category
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
        self._update_subtree_paths(old_path, new_path)

    @classmethod
    def move_subtree(cls, category_id, new_parent_id=None):
        category = cls.query.get(category_id)
        if not category:
            raise ValueError("Category not found")

        new_parent = cls.query.get(new_parent_id) if new_parent_id else None
        category.set_parent(new_parent)

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

    def get_possible_parents(self, cat: Category):
        max_d_parent = Category.MAX_DEPTH - cat.get_subtree_depth()
        return db.session.query(Category.id, Category.name).filter(
            Category.depth <= max_d_parent,
            ~Category.path.like(f"{cat.path}.%")
        ).all()

    def get_possible_children(self, cat: Category):
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

    def get_possible_parents_for_children(self, cat: Category):
        max_d_parent = Category.MAX_DEPTH - cat.get_subtree_depth() + 1

        possible_parents = db.session.query(Category.id, Category.name).filter(
            Category.depth <= max_d_parent,
            Category.id != cat.id,
            ~Category.path.like(f"{cat.path}.%")
        ).all()

        possible_parents.append((cat.id, cat.name))
        return possible_parents
# routes.py
# /templates