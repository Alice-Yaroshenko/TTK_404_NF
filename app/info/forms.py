from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed 
from wtforms.validators import DataRequired, Length, ValidationError
import os 

class ArticleForm(FlaskForm):
    title = StringField('Название статьи', validators=[
        DataRequired(message="Название не может быть пустым"),
        Length(min=3, max=200, message="Название должно содержать от 3 до 200 символов")
    ])
    content = TextAreaField('Содержание статьи', validators=[DataRequired(message="Содержание не может быть пустым")], render_kw={'rows': 15, 'id': 'article_content_editor'})

   
    image = FileField('Изображение для статьи (необязательно)')

    submit = SubmitField('Сохранить статью')

    def validate_image(self, field):
        """Проверяет расширение загруженного файла во время валидации."""
   
        if field.data:
            filename = field.data.filename
            if filename: 
                allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS')
                if not allowed_extensions:
                    current_app.logger.error("Конфигурация ALLOWED_EXTENSIONS не найдена!")
                    raise ValidationError("Ошибка конфигурации сервера: не заданы разрешенные расширения файлов.")

                is_allowed = '.' in filename and \
                             filename.rsplit('.', 1)[1].lower() in allowed_extensions

                if not is_allowed:
                    allowed_str = ", ".join(sorted(list(allowed_extensions)))
                    raise ValidationError(f'Разрешены только изображения форматов: {allowed_str}!')
