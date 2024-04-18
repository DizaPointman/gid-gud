from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from flask_login import UserMixin
from hashlib import md5

class User(UserMixin, db.Model):
    """
    Represents a user in the application.

    Attributes:
        id (int): The unique identifier for the user (primary key).
        username (str): The unique username of the user (maximum 64 characters).
        email (str): The unique email address of the user (maximum 120 characters).
        password_hash (str): The hashed password of the user (maximum 256 characters).

        gidguds (List[GidGud]): The list of gidguds authored by the user.
        categories (List[Category]): The list of categories owned by the user.

        about_me (str): A short description or bio of the user (maximum 140 characters).
        last_seen (datetime): The timestamp of the user's last activity.

    Methods:
        __repr__: Returns a string representation of the user object.
        set_password: Sets the user's password after hashing it.
        check_password: Checks if the provided password matches the user's hashed password.
        avatar: Generates a URL for the user's Gravatar image based on their email address.

    """
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    gidguds: so.WriteOnlyMapped['GidGud'] = so.relationship(back_populates='author')
    categories: so.Mapped[list['Category']] = so.relationship('Category', back_populates='user')

    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

class GidGud(db.Model):
    """
    Represents a GidGud (task) in the application.

    Attributes:
        id (int): The unique identifier for the GidGud (primary key).
        body (str): The description or content of the GidGud (maximum 140 characters).
        timestamp (datetime): The timestamp when the GidGud was created.
        user_id (int): The ID of the user who created the GidGud.

        recurrence (bool): Indicates if the GidGud has a recurrence pattern (default: False).
        recurrence_rhythm (int): The recurrence rhythm of the GidGud (default: 0).
        amount (int): The amount associated with the GidGud (default: 1).
        unit (str): The unit of measurement for the GidGud (maximum 10 characters, nullable).
        times (int): The number of times the GidGud has been completed (default: 1).

        completed (bool): Indicates if the GidGud has been completed (default: False).
        archived (bool): Indicates if the GidGud has been archived (default: False).

        category_id (int): The ID of the category associated with the GidGud.
        category (Category): The category associated with the GidGud.
        author (User): The user who authored the GidGud.

    Methods:
        __repr__: Returns a string representation of the GidGud object.

    """
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    recurrence: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    recurrence_rhythm: so.Mapped[int] = so.mapped_column(sa.Integer(), default=0)
    amount: so.Mapped[int] = so.mapped_column(sa.Integer(), default=1)
    unit: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=True)
    times: so.Mapped[int] = so.mapped_column(sa.Integer(), default=1)

    completed: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)

    category_id: so.Mapped[int] = so.mapped_column(sa.Integer, sa.ForeignKey('category.id'))
    category: so.Mapped['Category'] = so.relationship('Category', back_populates='gidguds')
    author: so.Mapped['User'] = so.relationship(back_populates='gidguds')

    def __repr__(self):
        return '<GidGud {}>'.format(self.body)

    # TODO: sanitizing gidgud attributes (whitespace characters at end or beginning) check other cases for problems

class Category(db.Model):
    """
    Represents a category in the application.

    Attributes:
        id (int): The unique identifier for the category (primary key).
        name (str): The name of the category (maximum 20 characters).
        user_id (int): The ID of the user who owns the category.
        user (User): The user who owns the category.
        parent_id (int): The ID of the parent category (nullable).
        parent (Category): The parent category (nullable).
        children (list[Category]): The list of child categories associated with this category.
        gidguds (list[GidGud]): The list of GidGuds associated with this category.

    Methods:
        __repr__: Returns a string representation of the Category object.

    """
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

    # TODO: add creation of 'default' category on user creation
    # TODO: sanitizing category names (whitespace characters at end or beginning) check other cases for problems
    # TODO: add protection for default?
    # TODO: prevent user from naming categories 0, Null, default, No Parent, No Children, None
    # TODO: assure prevented names can't be achieved by tricks, like other encodings, ASCII etc

@login.user_loader
def load_user(id):
    """
    Load a user object from the database.

    This function is used by Flask-Login to reload the user object from the user ID stored in the session.
    It retrieves the user object corresponding to the provided ID from the database.

    Args:
        id (int): The ID of the user to load.

    Returns:
        User or None: The user object corresponding to the provided ID, or None if no user with that ID is found.

    """
    return db.session.get(User, int(id))