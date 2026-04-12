import os
from base64 import b64decode
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.all_models import User, Character
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'character_hub_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
# если неавторизованный пользователь попытается зайти на защищенную страницу, его перекинет сюда:
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    db_sess = db_session.create_session()
    characters = db_sess.query(Character).all()
    return render_template('index.html', characters=characters)



@app.route('/register', methods=['GET', 'POST'])
def register():
    # Если уже вошел, то перекидываем на главную
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form, message="Такая почта уже есть")
        if db_sess.query(User).filter(User.username == form.username.data).first():
            return render_template('register.html', title='Регистрация', form=form, message="Такое имя уже занято")

        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('profile'))

    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('profile'))
        return render_template('login.html', message="Неправильный логин или пароль", form=form)

    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', title='Личный кабинет')


def add_data():
    """Добавляет тестовые данные"""
    db_sess = db_session.create_session()
    if not db_sess.query(Character).first():
        # Создаем тестового юзера (пароль: 123456)
        test_user = User(username="admin", email="admin@hub.local", hashed_password="pbkdf2:sha256:260000$sRHL68rPP0PtzOUj$c598e722c8e7c9904ab75ad768b276bdf7ec269ca7680e038d39858a6192a6d9")
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