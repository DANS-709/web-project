from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, TextAreaField, HiddenField, FieldList, FormField
from wtforms.validators import DataRequired, Optional


class AbilityForm(FlaskForm):
    name = StringField('Название')
    description = TextAreaField('Описание')
    effect = TextAreaField('Эффект')


class CharacterForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(message="Введите имя персонажа")])
    level = IntegerField('Уровень', default=1)
    hp = IntegerField('HP', default=100)
    strength = IntegerField('Сила', default=0)
    dexterity = IntegerField('Ловкость', default=0)
    intelligence = IntegerField('Интеллект', default=0)
    charisma = IntegerField('Харизма', default=0)
    race_name = StringField('Название расы')
    race_effect = StringField('Эффект расы')
    class_name = StringField('Название класса')
    class_effect = StringField('Эффект класса')
    image_file = FileField('Файл изображения', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения!')
    ])
    image_b64 = HiddenField('Base64 данные')
    abilities = FieldList(FormField(AbilityForm), min_entries=1)