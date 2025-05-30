from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.info import bp
from app.models import Article, ArticleHistory, User
from app.info.forms import ArticleForm
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, timezone
import os
import uuid
from werkzeug.utils import secure_filename
import bleach

def save_article_image(form_picture):
    """Сохраняет изображение статьи и возвращает имя файла."""
    random_hex = uuid.uuid4().hex
    filename, f_ext = os.path.splitext(secure_filename(form_picture.filename))
    picture_fn = random_hex + f_ext.lower()
    picture_path = os.path.join(current_app.root_path,
                                current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER'],
                                picture_fn)
    try:
        form_picture.save(picture_path)
        current_app.logger.debug(f"Файл сохранен: {picture_path}")
    except Exception as e:
         current_app.logger.error(f"Не удалось сохранить файл {picture_path}: {e}")
         return None
    return picture_fn

def sanitize_html(html_content):
    """Очищает HTML от небезопасных тегов и атрибутов."""
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 's', 'blockquote', 'code', 'pre',
        'ul', 'ol', 'li', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption'
    ]
    allowed_attrs = {
        '*': ['class', 'style', 'title', 'id'],
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'style', 'width', 'height'],
        'th': ['colspan', 'rowspan', 'scope'],
        'td': ['colspan', 'rowspan', 'scope'],
        'ol': ['start', 'type'],
        'ul': ['type'],
    }
    try:
        cleaned_html = bleach.clean(html_content,
                                    tags=allowed_tags,
                                    attributes=allowed_attrs,
                                    strip=True)
        return cleaned_html
    except Exception as e:
        current_app.logger.error(f"Ошибка при очистке HTML: {e}")
        return "<p><i>Ошибка обработки содержимого</i></p>"


@bp.route('/articles')
@login_required
def list_articles():
    page = request.args.get('page', 1, type=int)
    per_page = 9
    articles_pagination = Article.query.options(
            joinedload(Article.author),
            joinedload(Article.last_editor)
        ).filter(
            Article.is_deleted == False
        ).order_by(
            Article.updated_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    articles = articles_pagination.items
    form = ArticleForm() 
    return render_template(
        'info/articles.html',
        title='Полезная информация',
        articles=articles,
        pagination=articles_pagination,
        form=form
    )

@bp.route('/article/<int:article_id>')
@login_required
def view_article(article_id):
    article = Article.query.options(
        joinedload(Article.author),
        joinedload(Article.last_editor)
    ).get_or_404(article_id)
    if article.is_deleted and current_user.role != 'Администратор':
         flash('Эта статья была удалена.', 'warning')
         return redirect(url_for('info.list_articles'))
    form = ArticleForm() 
    return render_template(
        'info/article_view.html',
        title=article.title,
        article=article,
        form=form
        )

@bp.route('/articles/new', methods=['GET', 'POST'])
@login_required
def create_article():
    form = ArticleForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            try:
                image_filename = save_article_image(form.image.data)
                if not image_filename:
                     flash('Не удалось сохранить изображение.', 'danger')
            except Exception as e:
                current_app.logger.error(f"Ошибка при обработке изображения: {e}", exc_info=True)
                flash('Произошла ошибка при обработке изображения.', 'danger')
                image_filename = None

        sanitized_content = sanitize_html(form.content.data)

        try:
            article = Article(
                title=form.title.data,
                content=sanitized_content,
                author_id=current_user.id,
                last_editor_id=current_user.id,
                image_filename=image_filename
            )
            db.session.add(article)
            db.session.commit()
            history_entry = ArticleHistory(
                article_id=article.id,
                user_id=current_user.id,
                event_type='created'
            )
            db.session.add(history_entry)
            db.session.commit()
            flash('Статья успешно создана!', 'success')
            return redirect(url_for('info.view_article', article_id=article.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ошибка при создании статьи: {e}", exc_info=True)
            if image_filename:
                 try:
                     file_path = os.path.join(current_app.root_path, current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER'], image_filename)
                     if os.path.exists(file_path):
                        os.remove(file_path)
                        current_app.logger.info(f"Удален файл {image_filename} после ошибки создания статьи.")
                 except OSError as remove_error:
                     current_app.logger.error(f"Не удалось удалить файл {image_filename} после ошибки создания статьи: {remove_error}")
            flash('Произошла ошибка при создании статьи.', 'danger')

    return render_template(
        'info/article_form.html',
        title='Создание статьи',
        form=form,
        legend='Новая статья'
    )


@bp.route('/article/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    if article.is_deleted:
         flash('Нельзя редактировать удаленную статью.', 'danger')
         return redirect(url_for('info.list_articles'))
    if article.author_id != current_user.id and current_user.role != 'Администратор':
        abort(403)

    form = ArticleForm(obj=article if request.method == 'GET' else None)

    if form.validate_on_submit():
        new_image_filename = article.image_filename
        image_saved_successfully = True

        if form.image.data:
            try:
                saved_fn = save_article_image(form.image.data)
                if not saved_fn:
                     flash('Не удалось сохранить новое изображение. Оставлено старое (если было).', 'warning')
                     image_saved_successfully = False
                else:
                    new_image_filename = saved_fn
                    if article.image_filename and image_saved_successfully:
                         try:
                             old_image_path = os.path.join(current_app.root_path, current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER'], article.image_filename)
                             if os.path.exists(old_image_path):
                                 os.remove(old_image_path)
                                 current_app.logger.info(f"Удален старый файл {article.image_filename} при обновлении статьи {article_id}.")
                         except OSError as remove_error:
                             current_app.logger.error(f"Не удалось удалить старый файл {article.image_filename}: {remove_error}")
            except Exception as e:
                current_app.logger.error(f"Ошибка при обработке изображения при редактировании статьи {article_id}: {e}", exc_info=True)
                flash('Произошла ошибка при обработке изображения.', 'danger')
                image_saved_successfully = False

        sanitized_content = sanitize_html(form.content.data)

        try:
            article.title = form.title.data
            article.content = sanitized_content
            article.last_editor_id = current_user.id
            article.image_filename = new_image_filename
            db.session.add(article)
            history_entry = ArticleHistory(
                article_id=article.id,
                user_id=current_user.id,
                event_type='updated'
            )
            db.session.add(history_entry)
            db.session.commit()
            flash('Статья успешно обновлена!', 'success')
            return redirect(url_for('info.view_article', article_id=article.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ошибка при обновлении статьи ID={article_id}: {e}", exc_info=True)
            if form.image.data and new_image_filename != article.image_filename and image_saved_successfully:
                 try:
                     new_file_path = os.path.join(current_app.root_path, current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER'], new_image_filename)
                     if os.path.exists(new_file_path):
                        os.remove(new_file_path)
                        current_app.logger.info(f"Удален новый файл {new_image_filename} после ошибки обновления статьи.")
                 except OSError as remove_error:
                     current_app.logger.error(f"Не удалось удалить файл {new_image_filename} после ошибки обновления статьи: {remove_error}")
            flash('Произошла ошибка при обновлении статьи.', 'danger')

    current_image = article.image_filename
    return render_template(
        'info/article_form.html',
        title='Редактирование статьи',
        form=form,
        legend=f'Редактирование: {article.title}',
        article=article,
        current_image=current_image
    )

@bp.route('/article/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    if article.author_id != current_user.id and current_user.role != 'Администратор':
        abort(403)
    if article.is_deleted:
        flash('Статья уже была удалена.', 'info')
        return redirect(url_for('info.list_articles'))
    try:
        article.is_deleted = True
        article.deleted_at = datetime.now(timezone.utc)
        article.last_editor_id = current_user.id
        history_entry = ArticleHistory(
            article_id=article.id,
            user_id=current_user.id,
            event_type='deleted'
        )
        db.session.add(article)
        db.session.add(history_entry)
        db.session.commit()
        flash('Статья была удалена. Ее можно восстановить в течение 7 дней из истории.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при удалении статьи ID={article_id}: {e}", exc_info=True)
        flash('Произошла ошибка при удалении статьи.', 'danger')
    return redirect(url_for('info.list_articles'))

@bp.route('/articles/history')
@login_required
def article_history():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    history_pagination = ArticleHistory.query.options(
            joinedload(ArticleHistory.user),
            joinedload(ArticleHistory.article)
        ).order_by(
            ArticleHistory.timestamp.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    history_entries = history_pagination.items
    form = ArticleForm() 
    return render_template(
        'info/article_history.html',
        title='История изменений статей',
        entries=history_entries,
        pagination=history_pagination,
        form=form
    )

@bp.route('/article/<int:article_id>/restore', methods=['POST'])
@login_required
def restore_article(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user.role != 'Администратор':
         flash('Только администратор может восстанавливать статьи.', 'danger')
         return redirect(request.referrer or url_for('info.article_history'))
    if not article.is_deleted:
        flash('Эта статья не была удалена.', 'info')
        return redirect(request.referrer or url_for('info.article_history'))
    if article.deleted_at and (datetime.now(timezone.utc) - article.deleted_at) > timedelta(days=7):
        flash('Срок восстановления статьи (7 дней) истек.', 'danger')
        return redirect(request.referrer or url_for('info.article_history'))
    try:
        article.is_deleted = False
        article.deleted_at = None
        article.last_editor_id = current_user.id
        history_entry = ArticleHistory(
            article_id=article.id,
            user_id=current_user.id,
            event_type='restored'
        )
        db.session.add(article)
        db.session.add(history_entry)
        db.session.commit()
        flash('Статья успешно восстановлена!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка при восстановлении статьи ID={article_id}: {e}", exc_info=True)
        flash('Произошла ошибка при восстановлении статьи.', 'danger')
    return redirect(url_for('info.article_history'))
