from unicodedata import category
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from flask_login import UserMixin, current_user
from hashlib import md5
from pytz import utc

from sqlalchemy import select

#from app.managers.user_manager import create_default_root_category


#Create default category
def create_default_root_category(user):
        # Check if 'default' root category exists
        default_category = Category.query.filter_by(name='default', user_id=user.id).first()

        # If 'default' root category doesn't exist, create it
        if not default_category:
            default_category = Category(name='default', user=user)
            db.session.add(default_category)
            db.session.commit()

        return default_category

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
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.String(),
        index=True,
        default=iso_now
    )

    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
        # filter out gids and return only guds by: '& (GidGud.completed != None)'
        return (
            sa.select(GidGud)
            .join(GidGud.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id
            ) &
                sa.not_(GidGud.completed.is_(None)))
            .group_by(GidGud)
            .order_by(sa.func.datetime(GidGud.timestamp).desc())
        )

class GidGud(db.Model):

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        sa.String(),
        index=True,
        default=iso_now
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    recurrence_rhythm: so.Mapped[int] = so.mapped_column(sa.Integer(), default=0)
    time_unit: so.Mapped[Optional[str]] = so.mapped_column(sa.Enum('minutes', 'hours', 'days', 'weeks', 'months', nullable=True))
    next_occurrence: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.String(),
        index=True,
        nullable=True,
        default=None
    )

    amount: so.Mapped[int] = so.mapped_column(sa.Integer(), default=1)
    unit: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)
    times: so.Mapped[int] = so.mapped_column(sa.Integer(), default=1)

    completed: so.Mapped[datetime] = so.mapped_column(
        sa.String(),
        index=True,
        nullable=True,
        default=None
    )

    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)

    category_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('category.id'))
    category: so.Mapped['Category'] = so.relationship('Category', back_populates='gidguds')
    author: so.Mapped['User'] = so.relationship(back_populates='gidguds')

    def __repr__(self):
        return '<GidGud {}>'.format(self.body)

    # FIXME: rename recurrence to snooze: s_inter, s_unit, s_date
    # TODO: implement return next occurrence and delta for next occurrence

class Category(db.Model):

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(20))
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, db.ForeignKey('user.id'))
    user: so.Mapped['User'] = so.relationship('User', back_populates='categories')
    # Depth indicates own level
    depth: so.Mapped[int] = so.mapped_column(sa.Integer)
    # Height indicates level below
    height: so.Mapped[int] = so.mapped_column(sa.Integer)
    parent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), nullable=True)
    parent: so.Mapped[Optional['Category']] = so.relationship('Category', remote_side=[id])
    children: so.Mapped[list['Category']] = so.relationship('Category', back_populates='parent', remote_side=[parent_id], uselist=True)
    gidguds: so.Mapped[Optional[list['GidGud']]] = so.relationship('GidGud', back_populates='category')

    # Setting a tree height limit
    MAX_HEIGHT = 5

    def __repr__(self):
        return '<Category {}>'.format(self.name)

    """
    def __init__(self, name, user=None, parent=None):
        self.name = name
        self.user = user or current_user

        if parent is None and name != 'default':
            # Get or create default root category
            default_category = create_default_root_category(current_user)
            self.parent = default_category
            self.update_height_depth(default_category)
        else:
            self.parent = parent
            self.update_height_depth(parent)
    """

    def __init__(self, name, user=None, parent=None):
        self.name = name
        self.user = user or current_user

        if parent is None and name != 'default':
            # Get or create default root category
            default_category = create_default_root_category(current_user)
            self.parent = default_category
        else:
            self.parent = parent

    def update_depth(self):
        # apply to new parent
        self.depth = self.parent.depth + 1
        for child in self.children:
            child.update_depth()

    def update_height(self):
        # apply to old parent
        # apply to new parent
        if self.children:
            children_height = max(child.height for child in self.children)
            if children_height + 1 != self.height:
                self.height = children_height + 1
                if self.parent is not None:
                    self.parent.update_height()
        else:
            self.height = 1

    def update_height_depth(self, parent):

        if parent is None:
            self.height = 0  # Root category height
            self.depth = 5  # Root category depth
        else:
            # Update height
            self.height = parent.height + 1

            # Update depth
            if self.children:
                self.depth = max(child.depth for child in self.children) + 1
            else:
                self.depth = 1  # No children, depth is 1

            # Update parent depth
            parent.depth = max(parent.depth, self.depth + 1)
            # FIXME: This does not recursively wander up the tree

            # Update children height
            for child in self.children:
                child.update_height_depth(self)

    def get_possible_children(self):

        # Generate blacklist because ancestors can't be children
        blacklist = self.generate_blacklist_ancestors()
        # Filter out blacklisted categories and those that would violate MAX_DEPTH
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


@login.user_loader
def load_user(id):

    return db.session.get(User, int(id))
