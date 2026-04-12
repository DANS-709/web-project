import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    characters = orm.relationship("Character", back_populates='author')
    comments = orm.relationship("Comment", back_populates='user')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Character(SqlAlchemyBase):
    __tablename__ = 'characters'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    level = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    hp = sqlalchemy.Column(sqlalchemy.Integer, default=100)

    stats = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)
    abilities = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)
    race = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)
    character_class = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)

    image_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    author = orm.relationship('User', back_populates='characters')

    comments = orm.relationship('Comment', back_populates='character', cascade="all, delete, delete-orphan")
    likes = orm.relationship('Like', back_populates='character', cascade="all, delete, delete-orphan")


class Comment(SqlAlchemyBase):
    __tablename__ = 'comments'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=False)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    character_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("characters.id"))

    user = orm.relationship('User', back_populates='comments')
    character = orm.relationship('Character', back_populates='comments')


class Like(SqlAlchemyBase):
    __tablename__ = 'likes'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    character_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("characters.id"))

    character = orm.relationship('Character', back_populates='likes')