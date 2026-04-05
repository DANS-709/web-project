import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    # Связи
    characters = orm.relationship("Character", back_populates='author')
    comments = orm.relationship("Comment", back_populates='user')


class Character(SqlAlchemyBase):
    __tablename__ = 'characters'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    level = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    hp = sqlalchemy.Column(sqlalchemy.Integer, default=100)

    # JSON-поля
    stats = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)
    abilities = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)
    race = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)
    character_class = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)

    # изображение
    image_path = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    # Внешние ключи и связи
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