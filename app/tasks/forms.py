from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.fields import DateField 
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models import TASK_PRIORITIES, User

class TaskForm(FlaskForm):
    title = StringField('Название задачи', validators=[
        DataRequired(message="Название не может быть пустым"),
        Length(min=3, max=200, message="Название должно содержать от 3 до 200 символов")
    ])
    description = TextAreaField('Описание задачи', render_kw={'rows': 8})

    assignee_id = SelectField('Ответственный', coerce=int, validators=[Optional()])

    priority = SelectField('Приоритет', choices=TASK_PRIORITIES,
                           default=TASK_PRIORITIES[1], 
                           validators=[DataRequired(message="Выберите приоритет")])

    due_date = DateField('Плановая дата решения', format='%Y-%m-%d', validators=[Optional()])

    image = FileField('Изображение к задаче (необязательно)', validators=[

        Optional() 
    ])

    submit = SubmitField('Сохранить задачу')

    def validate_image(self, field):
        if field.data:
            filename = field.data.filename
            if filename:
                allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'}) 
                is_allowed = '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
                if not is_allowed:
                    allowed_str = ", ".join(sorted(list(allowed_extensions)))
                    raise ValidationError(f'Разрешены только изображения форматов: {allowed_str}!')


    def validate_assignee_id(self, field):
         if field.data and field.data != 0: 
             user = User.query.get(field.data)
             if not user or not user.is_active:
                 raise ValidationError('Выбран недействительный пользователь.')
