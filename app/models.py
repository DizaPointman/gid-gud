from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db

class User(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    todos: so.WriteOnlyMapped['ToDo'] = so.relationship(back_populates='author')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
class ToDo(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    recurrence: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    recurrence_rythm: so.Mapped[int] = so.mapped_column(sa.Integer(), default=0)
    completed: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)

    author: so.Mapped[User] = so.relationship(back_populates='todos')

    def __repr__(self):
        return '<Post {}>'.format(self.body)