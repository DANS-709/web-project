from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.all_models import User, Character
from forms.user import RegisterForm, LoginForm
import os
import base64
import uuid
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'character_hub_super_secret_key'
# Папка для сохранения картинок
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# Вспомогательные функции
def save_image_from_b64(b64_string):
    if not b64_string:
        return None
    try:
        if ',' in b64_string:
            b64_string = b64_string.split(',')[1]
        img_data = base64.b64decode(b64_string)
        filename = f"char_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(img_data)
        return f"images/{filename}"
    except Exception as e:
        print(f"Ошибка сохранения картинки: {e}")
        return None


def get_data(char):
    # Базовые поля
    char.name = request.form.get('name', 'Безымянный')
    char.level = int(request.form.get('level', 1))
    char.hp = int(request.form.get('hp', 100))
    # Раса и Класс
    char.race = [request.form.get('race_name', ''), request.form.get('race_effect', '')]
    char.character_class = [request.form.get('class_name', ''), request.form.get('class_effect', '')]
    # Характеристики
    char.stats = {
        "strength": int(request.form.get('strength', 0)),
        "dexterity": int(request.form.get('dexterity', 0)),
        "intelligence": int(request.form.get('intelligence', 0)),
        "charisma": int(request.form.get('charisma', 0))
    }
    # Способности
    ab_names = request.form.getlist('ability_name')
    ab_effects = request.form.getlist('ability_effect')
    ab_descs = request.form.getlist('ability_desc')
    abilities = []
    for i in range(len(ab_names)):
        if ab_names[i].strip():
            abilities.append({
                "name": ab_names[i],
                "effect": ab_effects[i] if i < len(ab_effects) else "",
                "description": ab_descs[i] if i < len(ab_descs) else ""
            })
    char.abilities = abilities


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


@app.route('/character/add', methods=['GET', 'POST'])
@login_required
def add_character():
    if request.method == 'POST':
        db_sess = db_session.create_session()
        char = Character(user_id=current_user.id)
        get_data(char)
        # Картинка
        b64_data = request.form.get('image_b64')
        img_file = request.files.get('image_file')
        if img_file and img_file.filename != '':
            filename = f"char_{uuid.uuid4().hex[:8]}_{secure_filename(img_file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img_file.save(filepath)
            char.image_path = f"images/{filename}"
        elif b64_data:
            char.image_path = save_image_from_b64(b64_data)
        db_sess.add(char)
        db_sess.commit()
        flash('Персонаж успешно добавлен!', 'success')
        return redirect(url_for('profile'))

    return render_template('character_form.html', title='Создание персонажа', character=None)


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


@app.route('/character/<int:char_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_character(char_id):
    db_sess = db_session.create_session()
    character = db_sess.query(Character).get(char_id)
    if not character:
        abort(404)
    if character.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        get_data(character)
        db_sess.commit()
        flash('Персонаж обновлен!', 'success')
        return redirect(url_for('view_character', char_id=character.id))

    return render_template('character_edit.html', title=f"Редактирование: {character.name}", character=character)


@app.route('/htmx/add-ability')
@login_required
def htmx_add_ability():
    return render_template('partials/ability_row.html')


@app.route('/character/load-json', methods=['POST'])
@login_required
def load_json_character():
    file = request.files.get('json_file')
    if not file:
        abort(404)
    try:
        data = json.load(file)
        db_sess = db_session.create_session()
        char = Character(user_id=current_user.id)
        # Базовые поля
        char.name = data.get('name', 'Безымянный')
        char.level = int(data.get('level', 1))
        char.hp = int(data.get('hp', 100))
        # Раса и Класс
        char.race = data.get('race', ['', ''])
        char.character_class = data.get('class', ['', ''])
        # Характеристики
        char.stats = data.get('stats', {'dexterity': 0, 'strength': 0, 'intelligence': 0, 'charisma': 0})
        char.abilities = data.get('abilities', [])
        # Картинка
        b64_data = data.get('image_b64')
        char.image_path = save_image_from_b64(b64_data)
        db_sess.add(char)
        db_sess.commit()
        flash('Персонаж успешно добавлен!', 'success')
        return '', 200, {'HX-Redirect': url_for('profile')}
    except Exception as e:
        return f'<div class="alert alert-danger">Ошибка JSON: {e}</div>', 400


if __name__ == '__main__':
    db_session.global_init("db/character_hub.sqlite")
    app.run(port=8080, host='127.0.0.1', debug=True)
