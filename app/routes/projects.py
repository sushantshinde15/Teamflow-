from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Project, ProjectMember, User, ActivityLog, Task, Message, TaskFile
from app.forms import ProjectForm
from app.utils import admin_required
from datetime import date


projects = Blueprint('projects', __name__)


@projects.route('/projects')
@login_required
def list_projects():

    if current_user.role == 'Admin':
        all_projects = Project.query.filter_by(created_by=current_user.id).order_by(Project.created_at.desc()).all()
    else:
        memberships = ProjectMember.query.filter_by(user_id=current_user.id).all()
        all_projects = []
        for m in memberships:
            all_projects.append(m.project)

    active_projects = []
    completed_projects = []
    for p in all_projects:
        if p.status == 'Completed':
            completed_projects.append(p)
        else:
            active_projects.append(p)

    return render_template('projects/list.html', projects=active_projects, completed_projects=completed_projects)


@projects.route('/project/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_project():

    form = ProjectForm()

    if form.validate_on_submit():
        project = Project()
        project.name = form.name.data
        project.description = form.description.data
        project.deadline = form.deadline.data
        project.priority = form.priority.data
        project.created_by = current_user.id
        db.session.add(project)
        db.session.flush()

        log = ActivityLog()
        log.project_id = project.id
        log.user_id = current_user.id
        log.action = 'Created project "' + project.name + '"'
        db.session.add(log)
        db.session.commit()

        flash('New project launched!', 'success')
        return redirect(url_for('projects.list_projects'))

    return render_template('projects/new_project.html', form=form)


@projects.route('/project/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_project(id):

    project = Project.query.get_or_404(id)
    form = ProjectForm(obj=project)

    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.deadline = form.deadline.data
        project.priority = form.priority.data
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('projects.view_project', id=id))

    return render_template('projects/edit_project.html', form=form, project=project)


@projects.route('/project/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'info')
    return redirect(url_for('projects.list_projects'))


@projects.route('/project/<int:id>/complete', methods=['POST'])
@login_required
@admin_required
def complete_project(id):

    project = Project.query.get_or_404(id)

    for task in project.tasks:
        if task.status != 'Completed':
            task.status = 'Completed'

    project.status = 'Completed'

    log = ActivityLog()
    log.project_id = id
    log.user_id = current_user.id
    log.action = 'Marked project "' + project.name + '" as completed'
    db.session.add(log)
    db.session.commit()

    flash('Project "' + project.name + '" marked as completed!', 'success')
    return redirect(url_for('projects.view_project', id=id))


@projects.route('/project/<int:id>/add-member', methods=['POST'])
@login_required
@admin_required
def add_member(id):

    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if user != None:
        already = ProjectMember.query.filter_by(project_id=id, user_id=user.id).first()
        if already == None:
            mem = ProjectMember()
            mem.project_id = id
            mem.user_id = user.id
            db.session.add(mem)

            log = ActivityLog()
            log.project_id = id
            log.user_id = current_user.id
            log.action = 'Added ' + user.full_name + ' to project'
            db.session.add(log)
            db.session.commit()

            flash(user.full_name + ' added to team.', 'success')
        else:
            flash('User already in project.', 'info')
    else:
        flash('No account found with that email.', 'danger')

    return redirect(url_for('projects.view_project', id=id))


@projects.route('/project/<int:id>/remove-member/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def remove_member(id, user_id):
    mem = ProjectMember.query.filter_by(project_id=id, user_id=user_id).first_or_404()
    db.session.delete(mem)
    db.session.commit()
    flash('Member removed from project.', 'info')
    return redirect(url_for('projects.view_project', id=id))


def get_task_chart_data(all_tasks):
    status_counts = {}
    priority_counts = {}
    member_workload = {}
    weekly = {}

    for task in all_tasks:
        s = task.status
        if s in status_counts:
            status_counts[s] += 1
        else:
            status_counts[s] = 1

        p = task.priority if task.priority != None else 'Low'
        if p in priority_counts:
            priority_counts[p] += 1
        else:
            priority_counts[p] = 1

        if task.assignee != None:
            name = task.assignee.full_name.split()[0]
            if name in member_workload:
                member_workload[name] += 1
            else:
                member_workload[name] = 1

        if task.status == 'Completed' and task.created_at != None:
            week = task.created_at.strftime('%b %d')
            if week in weekly:
                weekly[week] += 1
            else:
                weekly[week] = 1

    return status_counts, priority_counts, member_workload, weekly


@projects.route('/project/<int:id>')
@login_required
def view_project(id):

    project = Project.query.get_or_404(id)
    all_tasks = Task.query.filter_by(project_id=id).all()
    today = date.today()

    for task in all_tasks:
        if task.status != 'Completed':
            if task.deadline != None and task.deadline < today:
                task.status = 'Overdue'
    db.session.commit()

    total = len(all_tasks)
    done = sum(1 for t in all_tasks if t.status == 'Completed')
    progress = int((done / total) * 100) if total > 0 else 0

    kanban_columns = ['To Do', 'In Progress', 'Review', 'Completed', 'Overdue']
    tasks_by_status = {'To Do': [], 'In Progress': [], 'Review': [], 'Completed': [], 'Overdue': []}
    for task in all_tasks:
        if task.status in tasks_by_status:
            tasks_by_status[task.status].append(task)

    status_counts, priority_counts, member_workload, weekly = get_task_chart_data(all_tasks)

    chat_messages = Message.query.filter_by(project_id=id).order_by(Message.timestamp.asc()).limit(100).all()
    active_tab = request.args.get('tab', 'kanban')

    return render_template(
        'projects/view.html',
        project=project,
        tasks=all_tasks,
        progress=progress,
        tasks_by_status=tasks_by_status,
        kanban_columns=kanban_columns,
        status_counts=status_counts,
        priority_counts=priority_counts,
        member_workload=member_workload,
        weekly_completion=weekly,
        chat_messages=chat_messages,
        active_tab=active_tab,
        today=today
    )


@projects.route('/project/<int:id>/chat/send', methods=['POST'])
@login_required
def send_chat(id):

    project = Project.query.get_or_404(id)
    content = request.form.get('content', '').strip()

    if content != '':
        msg = Message()
        msg.sender_id = current_user.id
        msg.project_id = id
        msg.content = content
        db.session.add(msg)
        db.session.commit()

    return redirect(url_for('projects.view_project', id=id, tab='chat') + '#chat-bottom')
