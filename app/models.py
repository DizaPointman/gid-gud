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
    height: so.Mapped[int] = so.mapped_column(sa.Integer)
    depth: so.Mapped[int] = so.mapped_column(sa.Integer)
    parent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), nullable=True)
    parent: so.Mapped[Optional['Category']] = so.relationship('Category', remote_side=[id])
    children: so.Mapped[list['Category']] = so.relationship('Category', back_populates='parent', remote_side=[parent_id], uselist=True)
    gidguds: so.Mapped[Optional[list['GidGud']]] = so.relationship('GidGud', back_populates='category')

    # Setting a tree depth limit
    MAX_DEPTH = 5

    def __repr__(self):
        return '<Category {}>'.format(self.name)

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
            # FIXME: This does not recursively wander up the tree?
            #if parent.depth <= self.depth:
            #    parent.depth = self.depth + 1
            #    self.update_height_depth(parent)

            # Update children height
            for child in self.children:
                child.update_height_depth(self)

    # Perplexity
    def get_possible_children(self):
        # Alias for Category to use in recursive queries
        Parent = so.aliased(Category)

        # Define the initial non-recursive part of the CTE
        initial_query = db.session.query(Category.id, Category.parent_id).filter(Category.id == self.id)
        initial_query_cte = initial_query.cte(name='exclude_ancestors', recursive=True)

        # Define the recursive part of the CTE
        recursive_query = db.session.query(Parent.id, Parent.parent_id).join(
            initial_query_cte, Parent.parent_id == initial_query_cte.c.parent_id)

        # Combine them using a CTE
        exclude_ancestors_recursion = initial_query_cte.union_all(recursive_query)

        # Use the CTE in the final query
        exclude_ancestors_query = db.session.query(exclude_ancestors_recursion.c.id)

        # Explicitly create a select() construct for the subquery
        exclude_ancestors_subquery = exclude_ancestors_query.subquery()
        exclude_ancestors_select = select(exclude_ancestors_subquery.c.id)

        final_query = (
            db.session.query(Category)
            .filter(~Category.id.in_(exclude_ancestors_select))
            .where(Category.depth + self.height <= self.MAX_DEPTH)
            .all()
        )
        return final_query

    def get_possible_parents(self):
        # Alias for Category to use in recursive queries
        Child = so.aliased(Category)

        # Define the initial non-recursive part of the CTE
        initial_query = db.session.query(Category.id, Category.parent_id).filter(Category.id == self.id)
        initial_query_cte = initial_query.cte(name='exclude_descendants', recursive=True)

        # Define the recursive part of the CTE
        recursive_query = db.session.query(Child.id, Child.parent_id).join(
            initial_query_cte, Child.parent_id == initial_query_cte.c.parent_id)

        # Combine them using a CTE
        exclude_descendants_recursion = initial_query_cte.union_all(recursive_query)

        # Use the CTE in the final query
        exclude_descendants_query = db.session.query(exclude_descendants_recursion.c.id)

        # Explicitly create a select() construct for the subquery
        exclude_descendants_subquery = exclude_descendants_query.subquery()
        exclude_descendants_select = select(exclude_descendants_subquery.c.id)

        final_query = (
            db.session.query(Category)
            .filter(~Category.id.in_(exclude_descendants_select))
            .where(Category.height + self.depth <= self.MAX_DEPTH)
            .all()
        )
        return final_query


    # GPT
    def get_possible_children2(self):
        # Alias for Category to use in recursive queries
        Parent = so.aliased(Category)

        # Define the initial non-recursive part of the CTE
        initial_query = db.session.query(Category.id, Category.parent_id).filter(Category.id == self.id).subquery()

        # Define the recursive part of the CTE
        recursive_query = db.session.query(Parent.id, Parent.parent_id).join(
            initial_query, Parent.parent_id == initial_query.c.parent_id)

        # Combine them using a CTE
        exclude_ancestors_recursion = initial_query.cte(name='exclude_ancestors', recursive=True)
        exclude_ancestors_recursion = exclude_ancestors_recursion.union_all(recursive_query)

        # Use the CTE in the final query
        exclude_ancestors_query = db.session.query(exclude_ancestors_recursion.c.id)

        final_query = (
            db.session.query(Category)
            .filter(~Category.id.in_(exclude_ancestors_query))
            .filter(Category.depth + self.height <= self.MAX_DEPTH)
            .all()
        )
        return final_query

    def get_possible_parents2(self):
        # Alias for Category to use in recursive queries
        Child = so.aliased(Category)

        # Define the initial non-recursive part of the CTE
        initial_query = db.session.query(Category.id, Category.parent_id).filter(Category.id == self.id).subquery()

        # Define the recursive part of the CTE
        recursive_query = db.session.query(Child.id, Child.parent_id).join(
            initial_query, Child.parent_id == initial_query.c.parent_id)

        # Combine them using a CTE
        exclude_descendants_recursion = initial_query.cte(name='exclude_descendants', recursive=True)
        exclude_descendants_recursion = exclude_descendants_recursion.union_all(recursive_query)

        # Use the CTE in the final query
        exclude_descendants_query = db.session.query(exclude_descendants_recursion.c.id)

        final_query = (
            db.session.query(Category)
            .filter(~Category.id.in_(exclude_descendants_query))
            .filter(Category.height + self.depth <= self.MAX_DEPTH)
            .all()
        )
        return final_query

"""
    def get_possible_children(self):
        # Alias for Category to use in recursive queries
        Parent = so.aliased(Category)

        # Define the initial non-recursive part of the CTE
        initial_query = db.session.query(Category.id, Category.parent_id).filter(Category.id == self.id).subquery()

        # Define the recursive part of the CTE
        recursive_query = db.session.query(Parent.id, Parent.parent_id).join(
            initial_query, Parent.parent_id == initial_query.c.id)

        # Combine them using a CTE
        exclude_ancestors_recursion = initial_query.cte(name='exclude_ancestors', recursive=True)
        exclude_ancestors_recursion = exclude_ancestors_recursion.union_all(recursive_query)

        # Use the CTE in the final query
        exclude_ancestors_query = db.session.query(exclude_ancestors_recursion.c.id)

        final_query = (
            db.session.query(Category)
            .filter(~Category.id.in_(exclude_ancestors_query.subquery()))
            .where(Category.depth + self.height <= self.MAX_DEPTH)
            .all()
        )
        return final_query

    def get_possible_parents(self):
        # Alias for Category to use in recursive queries
        Child = so.aliased(Category)

        # Define the initial non-recursive part of the CTE
        initial_query = db.session.query(Category.id, Category.parent_id).filter(Category.id == self.id).subquery()

        # Define the recursive part of the CTE
        recursive_query = db.session.query(Child.id, Child.parent_id).join(
            initial_query, Child.parent_id == initial_query.c.id)

        # Combine them using a CTE
        exclude_descendants_recursion = initial_query.cte(name='exclude_descendants', recursive=True)
        exclude_descendants_recursion = exclude_descendants_recursion.union_all(recursive_query)

        # Use the CTE in the final query
        exclude_descendants_query = db.session.query(exclude_descendants_recursion.c.id)

        final_query = (
            db.session.query(Category)
            .filter(~Category.id.in_(exclude_descendants_query.subquery()))
            .where(Category.height + self.depth <= self.MAX_DEPTH)
            .all()
        )
        return final_query
"""

@login.user_loader
def load_user(id):

    return db.session.get(User, int(id))
