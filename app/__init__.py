import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, timezone

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    """Фабрика для создания экземпляра приложения Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class) 

    loaded_secret_key = app.config.get('SECRET_KEY')
    if not loaded_secret_key or loaded_secret_key == 'you-will-never-guess':
        app.logger.warning("Используется небезопасный или отсутствующий SECRET_KEY!")
    elif len(loaded_secret_key) < 16:
        app.logger.warning("SECRET_KEY слишком короткий!")

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    bcrypt.init_app(app)
    login_manager.init_app(app) 

    @app.context_processor
    def inject_utility_processor():
        return {
            'current_year': datetime.now().year, 
            'datetime': datetime, 
            'timedelta': timedelta, 
            'timezone': timezone, 
            'config': app.config 
            }
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth') 
    from app.main import bp as main_bp
    app.register_blueprint(main_bp) 
    from app.info import bp as info_bp
    app.register_blueprint(info_bp) 
    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks') 
    article_upload_folder = app.config.get('ARTICLE_IMAGE_UPLOAD_FOLDER')
    if article_upload_folder:
        article_upload_path = os.path.join(app.root_path, article_upload_folder)
        if not os.path.exists(article_upload_path):
            try:
                os.makedirs(article_upload_path)
                app.logger.info(f"Создана папка для загрузок статей: {article_upload_path}")
            except OSError as e:
                app.logger.error(f"Не удалось создать папку для загрузок статей {article_upload_path}: {e}")

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO) 
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    else:
        app.logger.setLevel(logging.DEBUG) 
        app.logger.info('Application startup in DEBUG mode')

    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Article, ArticleHistory, Task, TaskHistory
        return {
            'db': db,
            'User': User,
            'Article': Article, 'ArticleHistory': ArticleHistory,
            'Task': Task, 'TaskHistory': TaskHistory
            }

    return app 
from app import models
