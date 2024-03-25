from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import JSON
from sqlalchemy_json import NestedMutableJson
from app import db, login
from flask_login import UserMixin
from hashlib import md5

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    gids: so.WriteOnlyMapped['Gid'] = so.relationship(back_populates='author')
    guds: so.WriteOnlyMapped['Gud'] = so.relationship(back_populates='author')
    counter: so.Mapped[int] = so.mapped_column(default=1)
    categories: so.Mapped[dict[list]] = so.mapped_column(NestedMutableJson, default={})

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
    
    def categorize(self, category: str):
        number = self.counter

        if len(category) == 0:
            category = "uncategorized"

# if category in self.categories.items(): adds or exchanges number to list, but at least adds value to uncategorized, seems to overwrite values
# yes, overwrites instead of appends
# if category in self.categories: adds category and one value, doesnt update list with additional values


        if category in self.categories.items():
            self.categories[category].append(number)
            self.counter+=1
            return number
        
        else:
            self.categories[category] = [number]
            self.counter+=1
            return number
    
    def update_category(self, number, category):
        dict = self.categories
        if len(category) == 0:
            dict["uncategorized"] = number
        for k, v in dict.items():
            if category == k:
                v.append(number)
                return number
        dict[f"{category}"] = number
        return number
    
class Gid(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    number: so.Mapped[int] = so.mapped_column()

    recurrence: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    recurrence_rhythm: so.Mapped[int] = so.mapped_column(sa.Integer(), default=0)
    completed: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    archived: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)

    category: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=True)

    author: so.Mapped[User] = so.relationship(back_populates='gids')
    guds: so.WriteOnlyMapped['Gud'] = so.relationship(back_populates='gid')

    def __repr__(self):
        return '<Gid {}>'.format(self.body)
        
class Gud(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    gid_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Gid.id), index=True)
    number: so.Mapped[int] = so.mapped_column()

    category: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=True)

    author: so.Mapped[User] = so.relationship(back_populates='guds')
    gid: so.Mapped[Gid] = so.relationship(back_populates='guds')

    def __repr__(self):
        return '<Gud {}>'.format(self.body)
    
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))