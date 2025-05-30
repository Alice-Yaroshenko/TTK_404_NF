from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp
from app.models import User
import re 

class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired(message="Логин не может быть пустым")])
    password = PasswordField('Пароль', validators=[DataRequired(message="Пароль не может быть пустым")])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Вход')

class RegistrationForm(FlaskForm):
    login = StringField('Логин', validators=[
        DataRequired(message="Логин не может быть пустым"),
        Length(min=3, max=64, message="Логин должен содержать от 3 до 64 символов"),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Логин должен содержать только латинские буквы, '
               'цифры, точки или подчеркивания')
    ])
    full_name = StringField('ФИО', validators=[
        DataRequired(message="ФИО не может быть пустым"),
        Regexp(r'^[А-Яа-яЁё\s]+$', message='ФИО должно содержать только русские буквы и пробелы')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message="Пароль не может быть пустым"),
        Length(min=6, message="Пароль должен содержать минимум 6 символов"),
        Regexp(r'^[A-Za-z0-9!"#$%&\'()*+,-./:;<=>?@[\\\]^_`{|}~]+$',
               message='Пароль может содержать только латинские буквы, цифры и символы: !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')

    ])
    confirm_password = PasswordField('Повторите пароль', validators=[
        DataRequired(message="Повторите пароль"),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Зарегистрироваться')

    def validate_login(self, login):
        """Проверяет, не занят ли логин."""
        user = User.query.filter_by(login=login.data).first()
        if user is not None:
            raise ValidationError('Этот логин уже занят. Пожалуйста, выберите другой.')
