from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.tasks import bp 
from app.models import Task, TaskHistory, User, TASK_STATUSES, TASK_STATUS_CURRENT, TASK_STATUS_DEFERRED, TASK_STATUS_COMPLETED
from app.tasks.forms import TaskForm
from datetime import date
from sqlalchemy.orm import joinedload

@bp.route('/')
@login_required
def tasks_redirect():
    """Редиректит с /tasks/ на страницу текущих задач."""
    return redirect(url_for('tasks.list_tasks', status=TASK_STATUS_CURRENT))

@bp.route('/<string:status>') 
@login_required
def list_tasks(status):
    """Отображает список задач для указанного статуса."""
    if status not in TASK_STATUSES:
         current_app.logger.warning(f"Попытка доступа к задачам с неверным статусом: {status}")
         abort(404) 

    page = request.args.get('page', 1, type=int)
    per_page = 9

    try:
        tasks_pagination = Task.query.options(joinedload(Task.assignee)).filter(
            Task.status == status,
            Task.is_deleted == False
        ).order_by(
            Task.created_at.desc() 
        ).paginate(page=page, per_page=per_page, error_out=False)

        tasks = tasks_pagination.items

        counters = {
            'current': db.session.query(Task.id).filter(Task.status == TASK_STATUS_CURRENT, Task.is_deleted == False).count(),
            'deferred': db.session.query(Task.id).filter(Task.status == TASK_STATUS_DEFERRED, Task.is_deleted == False).count()
        }
    except Exception as e:
        current_app.logger.error(f"Ошибка при запросе задач со статусом {status}: {e}", exc_info=True)
        flash("Произошла ошибка при загрузке задач.", "danger")
        tasks = []
        tasks_pagination = None
        counters = {'current': 0, 'deferred': 0}

    status_display_names = {
        TASK_STATUS_CURRENT: 'Текущие',
        TASK_STATUS_DEFERRED: 'Отложенные',
        TASK_STATUS_COMPLETED: 'Выполненные'
    }

    return render_template(
        'tasks/tasks.html',
        title=f"Задачи: {status_display_names.get(status, status)}",
        tasks=tasks,
        status=status,
        status_display_names=status_display_names,
        counters=counters,
        pagination=tasks_pagination,
        date=date 
    )


@bp.route('/new', methods=['GET'])
@login_required
def create_task():
    """Отображает форму создания новой задачи."""
    form = TaskForm()
    try:
        users = User.query.filter_by(_is_active=True).order_by(User.full_name).all() 
        form.assignee_id.choices = [(0, '--- Не назначен ---')] + [(u.id, u.full_name) for u in users]
    except Exception as e:
        current_app.logger.error(f"Ошибка при загрузке пользователей для формы задачи: {e}", exc_info=True)
        flash("Произошла ошибка при загрузке данных для формы.", "danger")
        form.assignee_id.choices = [(0, '--- Ошибка загрузки ---')]

    return render_template('tasks/task_form.html', title="Создание задачи", form=form, legend="Новая задача")


@bp.route('/view/<int:task_id>')
@login_required
def view_task(task_id):
    """Отображает детальную информацию о задаче."""
    try:
        task = Task.query.options(
            joinedload(Task.creator), joinedload(Task.assignee)
            ).get_or_404(task_id) 

        if task.is_deleted:
            current_app.logger.warning(f"Попытка просмотра удаленной задачи ID={task_id}")
            abort(404) 

        return f"Просмотр задачи '{task.title}' (ID: {task.id}). Шаблон task_view.html еще не создан."
    except Exception as e:
         current_app.logger.error(f"Ошибка при загрузке задачи ID={task_id}: {e}", exc_info=True)
         abort(500) 
