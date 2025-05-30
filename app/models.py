from datetime import datetime, timezone, date 
from flask_login import UserMixin
from app import db, login_manager, bcrypt
from flask import current_app

@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    try:
        user_id_int = int(user_id)
    except ValueError:
        current_app.logger.warning(f"Попытка загрузить пользователя с невалидным ID: {user_id}")
        return None
    user = User.query.get(user_id_int)
    if not user:
        current_app.logger.debug(f"Не найден пользователь для загрузки сессии с ID: {user_id_int}")
    return user

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), index=True, unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Пользователь')
    registration_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    _is_active = db.Column('is_active', db.Boolean, default=True, index=True)

    articles_authored = db.relationship('Article', foreign_keys='Article.author_id', backref='author', lazy='dynamic')
    articles_edited = db.relationship('Article', foreign_keys='Article.last_editor_id', backref='last_editor', lazy='dynamic')
    article_history_entries = db.relationship('ArticleHistory', backref='user', lazy='dynamic')

    tasks_created = db.relationship('Task', foreign_keys='Task.creator_id', backref='creator', lazy='dynamic')
    tasks_assigned = db.relationship('Task', foreign_keys='Task.assignee_id', backref='assignee', lazy='dynamic')
    task_history_entries = db.relationship('TaskHistory', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        if not self.password_hash:
             return False
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
         self._is_active = value

    def __repr__(self):
        return f'<User {self.login} (ID: {self.id})>'


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_editor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_filename = db.Column(db.String(128), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    history = db.relationship('ArticleHistory', backref='article', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Article {self.title}>'

class ArticleHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    event_type = db.Column(db.String(50), nullable=False, index=True)
    changes = db.Column(db.Text, nullable=True)
    def __repr__(self):
        return f'<ArticleHistory {self.event_type} for Article {self.article_id} at {self.timestamp}>'


TASK_STATUS_CURRENT = 'Current'
TASK_STATUS_DEFERRED = 'Deferred'
TASK_STATUS_COMPLETED = 'Completed'
TASK_STATUSES = [TASK_STATUS_CURRENT, TASK_STATUS_DEFERRED, TASK_STATUS_COMPLETED]

TASK_PRIORITY_LOW = 'Низкий'
TASK_PRIORITY_MEDIUM = 'Средний'
TASK_PRIORITY_HIGH = 'Высокий'
TASK_PRIORITIES = [TASK_PRIORITY_LOW, TASK_PRIORITY_MEDIUM, TASK_PRIORITY_HIGH]

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    due_date = db.Column(db.Date, nullable=True, index=True) 
    priority = db.Column(db.String(50), nullable=False, default=TASK_PRIORITY_MEDIUM, index=True)
    status = db.Column(db.String(50), nullable=False, default=TASK_STATUS_CURRENT, index=True)
    image_filename = db.Column(db.String(128), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    history = db.relationship('TaskHistory', backref='task', lazy='dynamic', cascade="all, delete-orphan")


    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'

class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False, index=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    event_type = db.Column(db.String(50), nullable=False, index=True) 
    changes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<TaskHistory {self.event_type} for Task {self.task_id} at {self.timestamp}>'

