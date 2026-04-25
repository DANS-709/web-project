from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.all_models import User, Character
from forms.user import RegisterForm, LoginForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'character_hub_super_secret_key'
# Папка для сохранения картинок (пригодится потом)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    db_sess = db_session.create_session()
    characters = db_sess.query(Character).order_by(Character.id.desc()).all()
    return render_template('index.html', characters=characters)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if (db_sess.query(User).filter(User.email == form.email.data).first() or
                db_sess.query(User).filter(User.username == form.username.data).first()):
            flash('Пользователь с такими данными уже существует', 'danger')
            return render_template('register.html', title='Регистрация', form=form)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=form.remember_me.data)
        flash('Регистрация успешна!', 'success')
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
        flash('Неправильный логин или пароль', 'danger')
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


@app.route('/character/<int:char_id>')
def view_character(char_id):
    db_sess = db_session.create_session()
    character = db_sess.query(Character).get(char_id)
    if not character:
        abort(404)
    return render_template('character_detail.html', title=character.name, character=character)


@app.route('/character/<int:char_id>/delete', methods=['POST'])
@login_required
def delete_character(char_id):
    db_sess = db_session.create_session()
    character = db_sess.query(Character).get(char_id)
    if not character:
        abort(404)
    if character.user_id != current_user.id:
        abort(403)
    # Удаляем картинку
    if character.image_path:
        full_path = os.path.join('static', character.image_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    db_sess.delete(character)
    db_sess.commit()
    flash('Персонаж удален.', 'success')
    return redirect(url_for('profile'))


if __name__ == '__main__':
    db_session.global_init("db/character_hub.sqlite")
    app.run(port=8080, host='127.0.0.1', debug=True)
