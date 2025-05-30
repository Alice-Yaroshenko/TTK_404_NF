from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.forms import LoginForm, RegistrationForm
from app.models import User
from urllib.parse import urlparse
import traceback

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        login_attempt = form.login.data
        password_attempt = form.password.data
        current_app.logger.debug(f"Попытка входа пользователя: {login_attempt}")

        user = User.query.filter_by(login=login_attempt).first()

        if user:
            password_match = user.check_password(password_attempt)
            if password_match and user.is_active:
                login_successful = login_user(user, remember=form.remember_me.data)
                if login_successful:
                    flash(f'Добро пожаловать, {user.full_name}!', 'success')
                    next_page = request.args.get('next')
                    if not next_page or urlparse(next_page).netloc != '':
                        next_page = url_for('main.index')
                    current_app.logger.info(f"Успешный вход пользователя: {user.login}")
                    return redirect(next_page)
                else:
                    current_app.logger.error(f"login_user вернул False для пользователя ID={user.id}")
                    flash('Не удалось выполнить вход. Попробуйте еще раз.', 'danger')
                    return redirect(url_for('auth.login'))
            else:
                flash('Неверный логин или пароль.', 'danger')
                current_app.logger.warning(f"Неудачная попытка входа для пользователя: {login_attempt} (Пароль: {'совпал' if password_match else 'НЕ совпал'}, Активен: {user.is_active})")
                return redirect(url_for('auth.login'))
        else:
            flash('Неверный логин или пароль.', 'danger')
            current_app.logger.warning(f"Неудачная попытка входа: пользователь не найден '{login_attempt}'")
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html', title='Вход', form=form)


@bp.route('/logout')
@login_required
def logout():
    current_app.logger.debug(f"Выход пользователя ID={current_user.id}, Логин={current_user.login}")
    logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            login_reg = form.login.data
            current_app.logger.debug(f"Попытка регистрации пользователя {login_reg}")
            user = User(
                login=login_reg,
                full_name=form.full_name.data,
                role='Пользователь'
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            current_app.logger.info(f"Пользователь зарегистрирован: ID={user.id}, Логин={user.login}")
            if user.id is None:
                 current_app.logger.error(f"Пользователь {login_reg} не получил ID после коммита!")
                 flash('Произошла ошибка при сохранении пользователя. Попробуйте позже.', 'danger')
                 return redirect(url_for('auth.register'))

            current_app.logger.debug(f"Попытка автоматического входа для пользователя ID={user.id}")
            login_successful = login_user(user)
            if not login_successful:
                current_app.logger.error(f"Не удалось автоматически войти пользователем ID={user.id} после регистрации.")
                flash('Регистрация прошла, но не удалось автоматически войти. Пожалуйста, войдите вручную.', 'warning')
            else:
                flash('Поздравляем, вы успешно зарегистрировались!', 'success')

            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ошибка при регистрации пользователя {form.login.data}: {e}", exc_info=True)
            flash('Произошла ошибка на сервере при регистрации. Попробуйте позже.', 'danger')
            return render_template('auth/register.html', title='Регистрация', form=form)

    current_app.logger.debug(f"Отображение формы регистрации (GET или невалидный POST)")
    return render_template('auth/register.html', title='Регистрация', form=form)
