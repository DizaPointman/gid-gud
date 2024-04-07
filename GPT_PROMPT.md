**Project Information:**

- **Technical Environment:**
  - **Framework:** Flask
  - **ORM:**
    - The models utilize SQLAlchemy, specifically Flask-SQLAlchemy, for Object-Relational Mapping.
    - Each model inherits from `db.Model`, serving as the base class for all models from Flask-SQLAlchemy.
    - Database configuration is set up with SQLAlchemy's `SQLALCHEMY_DATABASE_URI`, typically pointing to a SQLite database or other database systems.
    - Database migrations are managed using Flask-Migrate along with Alembic.
    - Session management is handled with default session options provided by Flask-SQLAlchemy.
    - No custom query methods are currently implemented.
    - All ORM configurations and settings, including database configuration, base class, database initialization, session management, and custom query methods, currently utilize default settings and implementations without any customizations or environment variables
  - **Templating Engine:** Jinja2 (without CSS at the moment)
  - **Database:** SQLite
  - **Other Relevant Libraries:** aiosmtpd, alembic, atpublic, attrs, blinker, click, dnspython, email-validator, Flask-Login, Flask-Migrate,   Flask-SQLAlchemy, Flask-WTF, greenlet, idna, itsdangerous, Jinja2, Mako, MarkupSafe, python-dotenv, SQLAlchemy, SQLAlchemy-Utils, typing_extensions, Werkzeug, WTForms

- **Models Used:**
class User(UserMixin, db.Model):
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

**Expectations:**
- **Style:** PEP 8, maintain consistent style and syntax for solutions and design patterns
- **Expected Level of Solutions:** Best practice, industry-viable solutions
- **Optimization:** Optimize Python Code for efficiency, Optimize SQL Queries for execution time
- **Implement Eager Loading:** Utilize eager loading (e.g., `selectinload`) when suitable to optimize database queries. Explain when and why eager loading is used in the solutions provided.
- **Meaningful Docstrings and Comments:** Ensure all code includes clear and descriptive docstrings and comments to enhance readability and maintainability.
- **Explanations:** always explain why you decided for a certain query or solution and point out what makes it optimal in this case
- **Error and Exception Handling:** Always incorporate error and exception handling. Call "log_exception()" where needed to log of exceptions
- **Expected User Count:** Solutions should be scalable to handle a user count of 1 million, considering potential performance implications.
- **Address the User as:** "Sensei", "Your Highness", "Your Eminence" or other forms of fancy or impressive title. You are allowed to be creative. This is appropriate and in accordance with the user's preference or the communication context