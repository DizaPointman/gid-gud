from unicodedata import category
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from typing import Optional
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

class GidGud(db.Model):

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        sa.String(),
        index=True,
        default=iso_now
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    author: so.Mapped['User'] = so.relationship(back_populates='gidguds')

    category_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('category.id'))
    category: so.Mapped['Category'] = so.relationship('Category', back_populates='gidguds')

    # Recurrence
    rec_val: so.Mapped[int] = so.mapped_column(sa.Integer(), nullable=True, default=0)
    rec_unit: so.Mapped[Optional[str]] = so.mapped_column(sa.Enum('instantly', 'minutes', 'hours', 'days', 'weeks', 'months', 'years', default='instantly'))
    rec_next: so.Mapped[Optional[datetime]] = so.mapped_column(
        sa.String(),
        index=True,
        nullable=True,
        default=None
    )

    # Specification
    base_amount: so.Mapped[int] = so.mapped_column(sa.Integer(),nullable=True, default=0)
    amount: so.Mapped[int] = so.mapped_column(sa.Integer(), nullable=True, default=1)
    unit: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)
    times: so.Mapped[int] = so.mapped_column(sa.Integer(), nullable=True, default=1)

    completed_at: so.Mapped[list[datetime]] = so.mapped_column(
        sa.String(),
        index=True,
        nullable=True)

    modified_at: so.Mapped[datetime] = so.mapped_column(
        sa.String(),
        index=True,
        nullable=True)

    archived_at: so.Mapped[datetime] = so.mapped_column(
        sa.String(),
        index=True,
        nullable=True)

    deleted_at: so.Mapped[datetime] = so.mapped_column(
        sa.String(),
        index=True,
        nullable=True)


    def __repr__(self):
        return '<GidGud {}>'.format(self.body)
    
    # TODO: add init function to set correct defaults

    def add_completed_at_date(self, timestamp):
        if self.completed_at is None:
            self.completed_at = []
        self.completed_at.append(timestamp)
        return True

    def set_rec_next(self, timestamp):

        if self.rec_val == 1 and self.rec_unit == 'instantly':
            rec_next = timestamp
        else:
            delta = timedelta(**{self.rec_unit: self.rec_val})
            rec_next = (datetime.fromisoformat(timestamp) + delta).isoformat()
        return rec_next


class Category(db.Model):

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(20))
    user_id: so.Mapped[int] = so.mapped_column(sa.Integer, db.ForeignKey('user.id'))
    user: so.Mapped['User'] = so.relationship('User', back_populates='categories')

    parent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), nullable=True)
    parent: so.Mapped[Optional['Category']] = so.relationship('Category', remote_side=[id])
    children: so.Mapped[list['Category']] = so.relationship('Category', back_populates='parent', remote_side=[parent_id], uselist=True)
    gidguds: so.Mapped[Optional[list['GidGud']]] = so.relationship('GidGud', back_populates='category')

    # Tree
    # Depth indicates own level below default including self
    depth: so.Mapped[int] = so.mapped_column(sa.Integer(), default=1)
    # Height indicates levels below including self
    height: so.Mapped[int] = so.mapped_column(sa.Integer(), default=1)

    # Setting a tree height limit
    MAX_HEIGHT = 5

    def __repr__(self):
        return f'<Category {self.name}>'




@login.user_loader
def load_user(id):

    return db.session.get(User, int(id))

# Event listeners
