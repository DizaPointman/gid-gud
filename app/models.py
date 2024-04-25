import string
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from flask_login import UserMixin
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
    parent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), nullable=True)
    parent: so.Mapped[Optional['Category']] = so.relationship('Category', remote_side=[id])
    children: so.Mapped[list['Category']] = so.relationship('Category', back_populates='parent', remote_side=[parent_id], uselist=True)
    gidguds: so.Mapped[Optional[list['GidGud']]] = so.relationship('GidGud', back_populates='category')

    def __repr__(self):
        return '<Category {}>'.format(self.name)

    def get_tree_depth(self):
        """
        Recursively calculate the depth of the category tree starting from this category.

        Returns:
            int: The depth of the category tree.
        """
        if not self.children:  # Base case: if the category has no children, return 0
            return 0
        else:
            # Recursively calculate the depth of each child and find the maximum depth
            max_child_depth = max(child.get_tree_depth() for child in self.children)
            return 1 + max_child_depth  # Increment depth by 1 for the current category

    def get_possible_parents(self) -> list[dict]:
        """
        Get a list of possible parent categories based on the category tree depth.

        Returns:
            list[dict]: A list of dictionaries containing category IDs and names.
        """
        possible_parents = []

        tree_depth = self.get_tree_depth()

        # Base query to select all categories except the current one
        base_query = (
            db.session.query(Category.id, Category.name)
            .filter(Category.id != self.id)
        )

        if tree_depth == 2:
            # No parent possible except 'default'
            categories_query = base_query.filter(Category.name == 'default')

        elif tree_depth == 1:
            # Parent without grandparent possible, only 'default' category as grandparent allowed
            categories_query = base_query.filter(~Category.parent.has(parent_id=None))

        else:  # tree_depth == 0
            # Parent with grandparent possible, only 'default' category as great grandparent allowed
            categories_query = base_query.filter(~Category.parent.has(Category.parent.has(parent_id=None)))

        possible_parents = [{'id': category_id, 'name': category_name} for category_id, category_name in categories_query]
        return possible_parents

    def get_possible_parents_old(self) -> list[dict[int, str]]:

        # TODO: adjust queries to work like utils function

        possible_parents = []

        tree_depth = self.get_tree_depth()

        if tree_depth == 2:
            # No parent possible except 'default'
            categories_query = (
                db.session.query(Category.id, Category.name)
                .filter(Category.name == 'default')
            )

        if tree_depth == 1:
            # Parent without grandparent possible, only 'default' category as grandparent allowed
            categories_query = (
                db.session.query(Category.id, Category.name)
                .filter(~Category.parent.has(Category.parent.has(Category.name != 'default')))  # Exclude categories with a grandparent that is not 'default'
                .filter(Category.parent_id != self.id)   # Exclude the current category as a potential parent
            )

        if tree_depth == 0:
            # Parent with grandparent possible, only 'default' category as great grandparent allowed
            categories_query = (
                db.session.query(Category.id, Category.name)
                .filter(~Category.parent.has(Category.parent.has(Category.parent.has(Category.name != 'default'))))  # Exclude categories with a great grandparent that is not 'default'
                .filter(Category.parent_id != self.id)   # Exclude the current category as a potential parent
            )

        possible_parents = [{'id': category_id, 'name': category_name} for category_id, category_name in categories_query]
        return possible_parents

    def possible_children(self) -> list[str]:

        # TODO: adjust queries to work like utils function

        possible_children = []

        # Fetch categories with no parent, excluding the default category, the current category, and categories with grandchildren
        categories_query = (
            db.session.query(Category)
            .filter(~Category.name.in_([self.name, 'default']))  # Exclude current category and default category
            .filter(~Category.children.any(Category.children != None))  # Exclude categories with grandchildren
        )
        possible_children = [category.name for category in categories_query.all()]

        return possible_children

    # TODO: implement functions with queries to return possible parents, children, etc

@login.user_loader
def load_user(id):

    return db.session.get(User, int(id))
