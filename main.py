import os
from flask import Flask, render_template
from data import db_session
from data.all_models import User, Character
from base64 import b64decode

app = Flask(__name__)
app.config['SECRET_KEY'] = 'character_hub_secret_key'


@app.route('/')
def index():
    # Открываем сессию БД и получаем всех персонажей
    db_sess = db_session.create_session()
    characters = db_sess.query(Character).all()
    return render_template('index.html', characters=characters)


def add_data():
    """Добавляет тестовые данные"""
    db_sess = db_session.create_session()
    if not db_sess.query(Character).first():
        # Создаем тестового юзера
        test_user = User(username="admin", email="admin@hub.local", hashed_password="123")
        db_sess.add(test_user)
        db_sess.commit()
        image_path = os.path.join('static/images', 'test.png').replace('\\', '/')
        img_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY3jP4PgfAAWgA4Dzhh/vAAAAAElFTkSuQmCC"
        image_data = b64decode(img_base64)
        # Сохраняем файл
        with open(image_path, 'wb') as f:
            f.write(image_data)
        test_char1 = Character(
            name="Артур Педрагон",
            level=15,
            user_id=test_user.id,
            image_path= '../' + image_path
        )
        test_char2 = Character(
            name="Эльфийка Лира",
            level=8,
            user_id=test_user.id,
            image_path= '../' + image_path
        )

        db_sess.add_all([test_char1, test_char2])
        db_sess.commit()


if __name__ == '__main__':
    db_session.global_init("db/character_hub.sqlite")
    add_data()
    app.run(port=8080, host='127.0.0.1', debug=True)