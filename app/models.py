from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import JSON
from app import db, login
from flask_login import UserMixin
from hashlib import md5
import copy
from sqlalchemy.ext.mutable import MutableList

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    gidguds: so.WriteOnlyMapped['GidGud'] = so.relationship(back_populates='author')
    categories: so.Mapped[list[Category]] = so.relationship('Category', back_populates='author')

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
    
    def running_number(self):
        self.counter += 1
        return self.counter
    
class GidGud(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    recurrence: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    recurrence_rhythm: so.Mapped[int] = so.mapped_column(sa.Integer(), default=0)
    completed: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)

    category_id: so.Mapped[int] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'))
    category: so.Mapped[Category] = so.relationship('Category', back_populates='gidguds')
    author: so.Mapped[User] = so.relationship(back_populates='gidguds')

    def __repr__(self):
        return '<Gid {}>'.format(self.body)
    
class Category(db.Model):
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    author: so.Mapped[User] = so.relationship(back_populates='categories')
    parent_id: so.Mapped[int] = so.mapped_column(sa.Integer, db.ForeignKey('category.id'), nullable=True)
    parent: so.Mapped[Category] = so.relationship('Category', remote_side=[id], backref='children', nullable=True)
    children: so.Mapped[list[Category]] = so.relationship('Category', backref='parent', remote_side=[parent_id])
    gidguds: so.Mapped[list[GidGud]] = so.relationship('GidGud', back_populates='category')

    def __repr__(self):
        return '<Category {}r>'.format(self.name)
    
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))