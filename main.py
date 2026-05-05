from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.all_models import User, Character, Like, Comment
from forms.user import RegisterForm, LoginForm
from forms.character import CharacterForm
from PIL import Image
import os
import base64
import uuid
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'character_hub_super_secret_key'
# Папка для сохранения картинок
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
# Максимальный размер файла
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024 * 2  # 2 МБ
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
            return render_template('register.html', form=form)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=form.remember_me.data)
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('profile'))
    return render_template('register.html', form=form)


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
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/character/add', methods=['GET', 'POST'])
@login_required
def add_character():
    form = CharacterForm()
    if request.method == 'POST':
        db_sess = db_session.create_session()
        char = Character(user_id=current_user.id)
        get_data(char)
        b64_data = request.form.get('image_b64')
        img_file = request.files.get('image_file')
        if img_file and img_file.filename != '':
            try:
                image = Image.open(img_file)
                width, height = image.size
                if not (140 <= width <= 160 and 170 <= height <= 190) or not (20 <= height - width <= 40):
                    flash(
                        f'Изображение имеет неправильные размеры или соотношение сторон.'
                        f' Макс: 160×190 Мин: 140×170 Ваше: {width}×{height}','danger')
                    return render_template('character_form.html', form=form, character=None)
            except Exception as e:
                flash(f'Ошибка при работе с изображением: {e}', 'danger')
                return render_template('character_form.html', form=form, character=None)
            img_file.stream.seek(0)  # Сбрасываем указатель потока для повторного чтения (так просто надо)
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
    return render_template('character_form.html', form=form, character=None)


@app.route('/character/<int:char_id>')
def view_character(char_id):
    db_sess = db_session.create_session()
    character = db_sess.query(Character).get(char_id)
    if not character:
        abort(404)
    like = db_sess.query(Like).filter(Like.user_id == current_user.id, Like.character_id == char_id).first()
    if like:
        user_liked = True
    else:
        user_liked = False
    return render_template('character_detail.html', character=character, user_liked=user_liked)


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
    form = CharacterForm()
    db_sess = db_session.create_session()
    char = db_sess.query(Character).get(char_id)
    if not char:
        abort(404)
    if char.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        get_data(char)
        b64_data = request.form.get('image_b64')
        img_file = request.files.get('image_file')
        if img_file and img_file.filename != '':
            try:
                image = Image.open(img_file)
                width, height = image.size
                if not (140 <= width <= 160 and 170 <= height <= 190) or not (20 <= height - width <= 40):
                    flash(
                        f'Изображение имеет неправильные размеры или соотношение сторон.'
                        f' Макс: 160×190 Мин: 140×170 Ваше: {width}×{height}','danger')
                    return render_template('character_edit.html', form=form, character=char)
            except Exception as e:
                flash(f'Ошибка при работе с изображением: {e}', 'danger')
                return render_template('character_edit.html', form=form, character=char)
            img_file.stream.seek(0)  # Сбрасываем указатель потока для повторного чтения (так просто надо)
            filename = f"char_{uuid.uuid4().hex[:8]}_{secure_filename(img_file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img_file.save(filepath)
            char.image_path = f"images/{filename}"
        elif b64_data:
            char.image_path = save_image_from_b64(b64_data)
        db_sess.commit()
        flash('Персонаж обновлен!', 'success')
        return redirect(url_for('view_character', char_id=char.id))
    return render_template('character_edit.html', form=form, character=char)


@app.route('/htmx/add-ability')
@login_required
def htmx_add_ability():
    return render_template('partials/ability_row.html')


@app.route('/character/load-json', methods=['POST'])
@login_required
def load_json_character():
    file = request.files.get('json_file')
    if not file:
        return "", 204
    try:
        data = json.load(file)
        db_sess = db_session.create_session()
        char = Character(user_id=current_user.id)
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
    except Exception:
        abort(400)


@app.route('/character/<int:char_id>/like', methods=['POST'])
@login_required
def toggle_like(char_id):
    db_sess = db_session.create_session()
    character = db_sess.query(Character).get(char_id)
    if not character:
        abort(404)

    like = db_sess.query(Like).filter(Like.user_id == current_user.id, Like.character_id == char_id).first()

    if like:
        db_sess.delete(like)
        user_liked = False
    else:
        new_like = Like(user_id=current_user.id, character_id=char_id)
        db_sess.add(new_like)
        user_liked = True

    db_sess.commit()
    return render_template('partials/like_btn.html', character=character, user_liked=user_liked)


@app.route('/character/<int:char_id>/comment', methods=['POST'])
@login_required
def add_comment(char_id):
    text = request.form.get('text')
    if not text or not text.strip():
        return "", 204

    db_sess = db_session.create_session()
    character = db_sess.query(Character).get(char_id)

    comment = Comment(text=text.strip(), user_id=current_user.id, character_id=char_id)
    db_sess.add(comment)
    db_sess.commit()
    return render_template('partials/comments_list.html', character=character)


if __name__ == '__main__':
    db_session.global_init("db/character_hub.sqlite")
    app.run(port=8080, host='127.0.0.1', debug=True)
