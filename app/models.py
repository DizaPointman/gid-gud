from sqlite3 import IntegrityError
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.orm import validates
from app.factory import db, login
from flask_login import UserMixin, current_user
from hashlib import md5
from pytz import utc


# Define a function to generate ISO 8601 formatted strings as timestamps
def iso_now():
    return datetime.now(utc).isoformat()

followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)

class User(UserMixin, db.Model):

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    gidguds: so.WriteOnlyMapped['GidGud'] = so.relationship(back_populates='author')
    categories: so.Mapped[list['Category']] = so.relationship('Category', back_populates='user')
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, default=iso_now)

    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')

    created_at: so.Mapped[datetime] = so.mapped_column(sa.String(), index=True, default=iso_now)
    modified_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)
    archived_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)
    deleted_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    # Getters and Setters for datetime attributes
    @property
    def created_at_datetime(self) -> datetime:
        return datetime.fromisoformat(self.created_at) if self.created_at else None

    @created_at_datetime.setter
    def created_at_datetime(self, value: datetime):
        self.created_at = value.isoformat() if value else None

    @property
    def modified_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.modified_at) if self.modified_at else None

    @modified_at_datetime.setter
    def modified_at_datetime(self, value: Optional[datetime]):
        self.modified_at = value.isoformat() if value else None

    @property
    def archived_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.archived_at) if self.archived_at else None

    @archived_at_datetime.setter
    def archived_at_datetime(self, value: Optional[datetime]):
        self.archived_at = value.isoformat() if value else None

    @property
    def deleted_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.deleted_at) if self.deleted_at else None

    @deleted_at_datetime.setter
    def deleted_at_datetime(self, value: Optional[datetime]):
        self.deleted_at = value.isoformat() if value else None

    # Password hashing
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # User profile
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)

    def following_guds(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        # using sa.func.datetime() to convert the ISO string timestamp to a datetime object
        # within the SQL query before performing the desc() ordering operation
        # filter out gids and return only guds by: '& (GidGud.completed_at != None)'
        return (
            sa.select(GidGud)
            .join(GidGud.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id
            ) &
                sa.not_(GidGud.completed_at.is_(None)))
            .group_by(GidGud)
            .order_by(sa.func.datetime(GidGud.timestamp).desc())
        )

class Category(db.Model):

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, db.ForeignKey(User.id), index=True)
    user: so.Mapped['User'] = so.relationship('User', back_populates='categories')

    parent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), index=True, nullable=True)
    parent: so.Mapped[Optional['Category']] = so.relationship('Category', remote_side=[id])
    path = so.Mapped[str] = so.mapped_column(db.String(255), nullable=False, index=True)
    gidguds: so.Mapped[Optional[list['GidGud']]] = so.relationship('GidGud', back_populates='category')

    created_at: so.Mapped[datetime] = so.mapped_column(sa.String(), index=True, default=iso_now)
    modified_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)
    archived_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)
    deleted_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)

    # Not in use yet
    a_brief_history_of_time = sa.Column(sa.String(255), nullable=True)

    # Setting a tree height limit
    MAX_HEIGHT = 5

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
            sa.func.max(
                sa.func.length(Category.path) - sa.func.length(sa.func.replace(Category.path, '.', '')) + 1
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
                    sa.update(Category)
                    .where(Category.path.like(f"{old_path}.%"))
                    .values(
                        path=sa.func.concat(
                            new_path,
                            sa.func.substr(Category.path, sa.func.length(old_path) + 1)
                        )
                    )
                )

                # Update the category's own path
                db.session.execute(
                    sa.update(Category)
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

    # Not in use yet
    def archive_and_historize(self, new_version):

        # Archive the old category
        self.archived_at_datetime = datetime.now(utc)

        # Set the history path
        if self.a_brief_history_of_time:
            new_version.a_brief_history_of_time = f"{self.a_brief_history_of_time}/{new_version.id}"
        else:
            self.a_brief_history_of_time = f"{self.id}"
            new_version.a_brief_history_of_time = f"{self.id}/{new_version.id}"

        db.session.commit()

        return True

    def get_version_history(self) -> List['Category']:
        if not self.a_history_of_violence:
            return [self]

        version_ids = [int(id) for id in self.a_brief_history_of_time.split('/')]
        return db.session.query(Category).filter(Category.id.in_(version_ids)).all()

    def __repr__(self):
        return f'<Category {self.name}>'

    # Getters and Setters for datetime attributes
    @property
    def created_at_datetime(self) -> datetime:
        return datetime.fromisoformat(self.created_at) if self.created_at else None

    @created_at_datetime.setter
    def created_at_datetime(self, value: datetime):
        self.created_at = value.isoformat() if value else None

    @property
    def modified_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.modified_at) if self.modified_at else None

    @modified_at_datetime.setter
    def modified_at_datetime(self, value: Optional[datetime]):
        self.modified_at = value.isoformat() if value else None

    @property
    def archived_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.archived_at) if self.archived_at else None

    @archived_at_datetime.setter
    def archived_at_datetime(self, value: Optional[datetime]):
        self.archived_at = value.isoformat() if value else None

    @property
    def deleted_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.deleted_at) if self.deleted_at else None

    @deleted_at_datetime.setter
    def deleted_at_datetime(self, value: Optional[datetime]):
        self.deleted_at = value.isoformat() if value else None


class GidGud(db.Model):

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    author: so.Mapped['User'] = so.relationship(back_populates='gidguds')

    category_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey(Category.id), index=True)
    category: so.Mapped['Category'] = so.relationship('Category', back_populates='gidguds')
    completions: so.Mapped[list['CompletionTable']] = so.relationship('CompletionTable', back_populates='gidgud', cascade="all, delete-orphan", lazy=True)

    # Recurrence
    rec: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, index=True)
    rec_val: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer(), default=0, nullable=True)
    rec_unit: so.Mapped[Optional[str]] = so.mapped_column(sa.Enum('minutes', 'hours', 'days', 'weeks', 'months', 'years', name="recurrence_units"), default='days', nullable=True)
    rec_next: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)

    # Specification
    # Add type (weight, time, money, distance, whatever)
    # TODO: implement type/unit templates
    # TODO: implement custom type/unit template creation with own units and exchange rates
    type_of_unit: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10), nullable=True)
    base_amount: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer(), nullable=True)
    amount: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer(), nullable=True)
    unit: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10), nullable=True)
    times: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer(), nullable=True)

    created_at: so.Mapped[datetime] = so.mapped_column(sa.String(), index=True, default=iso_now)
    modified_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)
    archived_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)
    deleted_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)

    # Materialized path for versioning
    a_history_of_violence = sa.Column(sa.String(255), nullable=True)

    def __repr__(self):
        return '<GidGud {}>'.format(self.body)


    def archive_and_historize(self, new_version):

        # Archive the old category
        self.archived_at_datetime = datetime.now(utc)

        # Set the history path
        if self.a_history_of_violence:
            new_version.a_history_of_violence = f"{self.a_history_of_violence}/{new_version.id}"
        else:
            self.a_history_of_violence = f"{self.id}"
            new_version.a_history_of_violence = f"{self.id}/{new_version.id}"

        self.rec_val, self.rec_unit, self.rec_next = None, None, None
        db.session.commit()

        return True


    def get_version_history(self) -> List['GidGud']:
        if not self.a_history_of_violence:
            return [self]
        version_ids = [int(id) for id in self.a_history_of_violence.split('/')]
        return db.session.query(GidGud).filter(GidGud.id.in_(version_ids)).all()


    # Getters and Setters for datetime attributes
    @property
    def rec_next_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.rec_next) if self.rec_next else None

    @rec_next_datetime.setter
    def rec_next_datetime(self, value: Optional[datetime]):
        self.rec_next = value.isoformat() if value else None

    @property
    def created_at_datetime(self) -> datetime:
        return datetime.fromisoformat(self.created_at) if self.created_at else None

    @created_at_datetime.setter
    def created_at_datetime(self, value: datetime):
        self.created_at = value.isoformat() if value else None

    @property
    def modified_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.modified_at) if self.modified_at else None

    @modified_at_datetime.setter
    def modified_at_datetime(self, value: Optional[datetime]):
        self.modified_at = value.isoformat() if value else None

    @property
    def archived_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.archived_at) if self.archived_at else None

    @archived_at_datetime.setter
    def archived_at_datetime(self, value: Optional[datetime]):
        self.archived_at = value.isoformat() if value else None

    @property
    def deleted_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.deleted_at) if self.deleted_at else None

    @deleted_at_datetime.setter
    def deleted_at_datetime(self, value: Optional[datetime]):
        self.deleted_at = value.isoformat() if value else None

    # GidGud methods

    def update_rec_next(self, timestamp: datetime):
        if self.rec:
            if self.rec_unit == 'months':
                # Handle months separately as timedelta doesn't support months
                rec_next = timestamp + relativedelta(months=self.rec_val)
            elif self.rec_unit == 'years':
                # Handle years separately as timedelta doesn't support years
                rec_next = timestamp + relativedelta(years=self.rec_val)
            else:
                # For other units, use timedelta
                delta = timedelta(**{self.rec_unit: self.rec_val})
                rec_next = timestamp + delta

            self.rec_next_datetime = rec_next
        else:
            self.rec_next_datetime = None

        db.session.commit()
        return self.rec_next_datetime

    def add_completion_entry(self, timestamp: datetime, custom_data=None):

        completion = CompletionTable(
            gidgud_id=self.id,
            user_id=self.user_id,
            body=self.body,
            category_name=self.category.name,
            category_id=self.category_id,
            completed_at=timestamp.isoformat()
        )

        # TODO: Make use of dictionary override in object
        # add , **custom_data and it will override every attribute that's provided in custom_data
        """
        type_of_unit=custom_data.get('type_of_unit', self.type_of_unit),
        base_amount=custom_data.get('base_amount', self.base_amount),
        amount=custom_data.get('amount', self.amount),
        unit=custom_data.get('unit', self.unit),
        times=custom_data.get('times', self.times),
        """

        db.session.add(completion)
        db.session.commit()

        return completion


class CompletionTable(db.Model):

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    gidgud_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(GidGud.id, ondelete="CASCADE"), nullable=False)
    gidgud: so.Mapped['GidGud'] = so.relationship('GidGud', back_populates='completions')
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), nullable=False)
    category_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Category.id), index=True, nullable=False)

    category_name: so.Mapped[str] = so.mapped_column(sa.String(), nullable=False)
    body: so.Mapped[str] = so.mapped_column(sa.String(), nullable=False)
    completed_at: so.Mapped[datetime] = so.mapped_column(sa.String(), index=True, nullable=False, default=iso_now)

    # Custom_data
    type_of_unit: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10), nullable=True)
    base_amount: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer(), nullable=True)
    amount: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer(), nullable=True)
    unit: so.Mapped[Optional[str]] = so.mapped_column(sa.String(10), nullable=True)
    times: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer(), nullable=True)

    deleted_at: so.Mapped[Optional[datetime]] = so.mapped_column(sa.String(), index=True, nullable=True)


    @property
    def completed_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.completed_at) if self.completed_at else None

    @completed_at_datetime.setter
    def completed_at_datetime(self, value: Optional[datetime]):
        self.completed_at = value.isoformat() if value else None

    @property
    def deleted_at_datetime(self) -> Optional[datetime]:
        return datetime.fromisoformat(self.deleted_at) if self.deleted_at else None

    @deleted_at_datetime.setter
    def deleted_at_datetime(self, value: Optional[datetime]):
        self.deleted_at = value.isoformat() if value else None

    def get_completed_gidguds():
        return db.session.query(CompletionTable).order_by(CompletionTable.completed_at).all()


@login.user_loader
def load_user(id):

    return db.session.get(User, int(id))

# Event listeners
