from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from datetime import date
import os
import secrets
from app import db, csrf
from app.models import Task, Project, ProjectMember, TaskReport, User, ActivityLog, TaskFile
from app.forms import TaskForm, ReportForm
from app.utils import admin_required


tasks = Blueprint('tasks', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'zip', 'py', 'js', 'html', 'css', 'mp4', 'mov'}


def allowed_file(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ALLOWED_EXTENSIONS:
        return True
    return False


@tasks.route('/kanban')
@login_required
def kanban():
    return redirect(url_for('projects.list_projects'))


@tasks.route('/project/<int:project_id>/task/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_task(project_id):

    project = Project.query.get_or_404(project_id)
    form = TaskForm()

    mems = ProjectMember.query.filter_by(project_id=project_id).all()
    choices = []
    for m in mems:
        choices.append((m.user.id, m.user.full_name))
    form.assigned_to.choices = choices

    if form.validate_on_submit():

        task = Task()
        task.project_id = project_id
        task.title = form.title.data
        task.description = form.description.data
        task.assigned_to = form.assigned_to.data
        task.priority = form.priority.data
        task.deadline = form.deadline.data
        db.session.add(task)

        log = ActivityLog()
        log.project_id = project_id
        log.user_id = current_user.id
        log.action = 'Created task "' + task.title + '"'
        db.session.add(log)

        db.session.commit()
        flash('Task assigned successfully.', 'success')
        return redirect(url_for('projects.view_project', id=project_id, tab='kanban'))

    return render_template('tasks/new_task.html', form=form, project=project)


@tasks.route('/task/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_task(id):

    task = Task.query.get_or_404(id)
    form = TaskForm(obj=task)

    # gotta repopulate the dropdown again here too
    mems = ProjectMember.query.filter_by(project_id=task.project_id).all()
    choices = []
    for m in mems:
        choices.append((m.user.id, m.user.full_name))
    form.assigned_to.choices = choices

    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.assigned_to = form.assigned_to.data
        task.priority = form.priority.data
        task.deadline = form.deadline.data
        db.session.commit()
        flash('Task updated.', 'success')
        return redirect(url_for('projects.view_project', id=task.project_id, tab='kanban'))

    return render_template('tasks/edit_task.html', form=form, task=task)


@tasks.route('/task/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task removed.', 'info')
    return redirect(url_for('projects.view_project', id=project_id, tab='kanban'))


# this one is called from the kanban drag and drop
@tasks.route('/task/move', methods=['POST'])
@csrf.exempt
@login_required
def move_task():

    data = request.get_json()

    if data == None:
        return jsonify({"success": False}), 400

    task = Task.query.get(data['task_id'])

    if task == None:
        return jsonify({"success": False}), 404

    is_admin = current_user.role == 'Admin'
    is_assignee = task.assigned_to == current_user.id

    if is_admin or is_assignee:
        task.status = data['new_status']

        if data['new_status'] == 'Completed':
            if task.report == None:
                auto_report = TaskReport()
                auto_report.task_id = task.id
                auto_report.member_id = current_user.id
                auto_report.summary = 'Task marked as completed.'
                auto_report.changes_made = ''
                auto_report.time_taken = ''
                db.session.add(auto_report)

        log = ActivityLog()
        log.project_id = task.project_id
        log.user_id = current_user.id
        log.action = 'Moved task "' + task.title + '" to ' + data['new_status']
        db.session.add(log)

        db.session.commit()
        return jsonify({"success": True})

    return jsonify({"success": False}), 403


@tasks.route('/task/<int:id>/detail')
@login_required
def task_detail(id):

    task = Task.query.get_or_404(id)

    files = []
    for f in task.files:
        file_info = {}
        file_info['id'] = f.id
        file_info['original_name'] = f.original_name
        file_info['uploaded_by'] = f.uploader.full_name
        file_info['uploaded_at'] = f.uploaded_at.strftime('%b %d, %Y %H:%M')
        file_info['file_size'] = get_human_readable_size(f.file_size or 0)
        file_info['download_url'] = url_for('tasks.download_file', file_id=f.id)
        files.append(file_info)

    if task.deadline != None:
        deadline_str = task.deadline.strftime('%b %d, %Y')
    else:
        deadline_str = '—'

    if task.assignee != None:
        assignee_name = task.assignee.full_name
        assignee_initial = task.assignee.full_name[0].upper()
    else:
        assignee_name = '—'
        assignee_initial = '?'

    if task.created_at != None:
        created_str = task.created_at.strftime('%b %d, %Y')
    else:
        created_str = '—'

    if task.priority != None:
        priority = task.priority
    else:
        priority = 'Low'

    is_project_admin = current_user.role == 'Admin' and task.project.created_by == current_user.id
    is_assignee = task.assigned_to == current_user.id
    can_upload = is_project_admin or is_assignee

    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description or '',
        'status': task.status,
        'priority': priority,
        'deadline': deadline_str,
        'assignee': assignee_name,
        'assignee_initial': assignee_initial,
        'created_at': created_str,
        'files': files,
        'can_upload': can_upload,
        'can_view_files': True,
        'can_edit': current_user.role == 'Admin',
        'project_id': task.project_id,
        'upload_url': url_for('tasks.upload_file', task_id=task.id),
        'report_url': url_for('tasks.submit_report', id=task.id),
        'edit_url': url_for('tasks.edit_task', id=task.id),
    })


@tasks.route('/task/<int:task_id>/upload', methods=['POST'])
@csrf.exempt
@login_required
def upload_file(task_id):

    task = Task.query.get_or_404(task_id)

    is_project_admin = current_user.role == 'Admin' and task.project.created_by == current_user.id
    is_assignee = task.assigned_to == current_user.id

    if is_project_admin == False and is_assignee == False:
        return jsonify({'success': False, 'error': 'Not authorized'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file sent'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    stored_name = secrets.token_hex(12) + '.' + ext

    upload_dir = os.path.join(
        current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
        'tasks',
        str(task_id)
    )

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    save_path = os.path.join(upload_dir, stored_name)
    file.save(save_path)

    file_size = os.path.getsize(save_path)

    tf = TaskFile()
    tf.task_id = task_id
    tf.uploaded_by = current_user.id
    tf.filename = stored_name
    tf.original_name = file.filename
    tf.file_size = file_size
    db.session.add(tf)

    log = ActivityLog()
    log.project_id = task.project_id
    log.user_id = current_user.id
    log.action = 'Uploaded "' + file.filename + '" to task "' + task.title + '"'
    db.session.add(log)

    db.session.commit()

    return jsonify({
        'success': True,
        'file': {
            'id': tf.id,
            'original_name': tf.original_name,
            'uploaded_by': current_user.full_name,
            'uploaded_at': tf.uploaded_at.strftime('%b %d, %Y %H:%M'),
            'file_size': get_human_readable_size(file_size),
            'download_url': url_for('tasks.download_file', file_id=tf.id)
        }
    })


@tasks.route('/task/file/<int:file_id>/download')
@login_required
def download_file(file_id):

    tf = TaskFile.query.get_or_404(file_id)
    task = Task.query.get_or_404(tf.task_id)

    is_project_admin = current_user.role == 'Admin' and task.project.created_by == current_user.id
    is_assignee = task.assigned_to == current_user.id
    is_project_member = ProjectMember.query.filter_by(project_id=task.project_id, user_id=current_user.id).first()

    if is_project_admin == False and is_assignee == False and is_project_member == None:
        return jsonify({'error': 'Not authorized'}), 403

    upload_dir = os.path.join(
        current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
        'tasks',
        str(tf.task_id)
    )

    return send_from_directory(upload_dir, tf.filename, as_attachment=True, download_name=tf.original_name)


@tasks.route('/task/<int:id>/submit-report', methods=['GET', 'POST'])
@login_required
def submit_report(id):

    task = Task.query.get_or_404(id)
    form = ReportForm()

    if form.validate_on_submit():

        report = TaskReport()
        report.task_id = id
        report.member_id = current_user.id
        report.summary = form.summary.data
        report.changes_made = form.changes_made.data
        report.time_taken = form.time_taken.data
        task.status = 'Completed'
        db.session.add(report)

        log = ActivityLog()
        log.project_id = task.project_id
        log.user_id = current_user.id
        log.action = 'Completed task "' + task.title + '"'
        db.session.add(log)

        db.session.commit()
        flash('Report submitted. Great job!', 'success')
        return redirect(url_for('projects.view_project', id=task.project_id, tab='kanban'))

    return render_template('tasks/report_form.html', form=form, task=task)


@tasks.route('/reports')
@login_required
def all_reports():

    if current_user.role == 'Admin':
        my_projects = Project.query.filter_by(created_by=current_user.id).all()
        my_project_ids = []
        for p in my_projects:
            my_project_ids.append(p.id)

        reports = TaskReport.query.join(Task).filter(
            Task.project_id.in_(my_project_ids)
        ).order_by(TaskReport.submitted_at.desc()).all()

    else:
        my_project_ids = []
        for m in current_user.member_of:
            my_project_ids.append(m.project_id)

        reports = TaskReport.query.filter_by(member_id=current_user.id).join(Task).filter(
            Task.project_id.in_(my_project_ids)
        ).order_by(TaskReport.submitted_at.desc()).all()

    return render_template('tasks/all_reports.html', reports=reports)


@tasks.route('/reports/<int:id>')
@login_required
def view_report(id):
    report = TaskReport.query.get_or_404(id)
    return render_template('tasks/view_report.html', report=report)


def get_human_readable_size(size_bytes):
    if size_bytes < 1024:
        return str(size_bytes) + ' B'
    elif size_bytes < 1024 * 1024:
        kb = size_bytes / 1024
        return str(round(kb, 1)) + ' KB'
    else:
        mb = size_bytes / (1024 * 1024)
        return str(round(mb, 1)) + ' MB'
