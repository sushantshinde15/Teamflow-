from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Project, Task, User, ActivityLog
from sqlalchemy import func
from app import db
from datetime import date


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return redirect(url_for('main.dashboard'))


@main.route('/dashboard')
@login_required
def dashboard():

    if current_user.role == 'Admin':
        my_projects = Project.query.filter_by(created_by=current_user.id).all()

        my_project_ids = [p.id for p in my_projects]
        proj_count = len(my_project_ids)

        task_count = 0
        done_count = 0
        for p in my_projects:
            for t in p.tasks:
                task_count += 1
                if t.status == 'Completed':
                    done_count += 1

        completed_projects = [p for p in my_projects if p.status == 'Completed']

    else:
        my_project_ids = []
        for m in current_user.member_of:
            my_project_ids.append(m.project_id)

        proj_count = len(my_project_ids)

        all_my_tasks = Task.query.filter_by(assigned_to=current_user.id).all()
        task_count = len(all_my_tasks)

        done_count = 0
        for t in all_my_tasks:
            if t.status == 'Completed':
                done_count = done_count + 1

        completed_projects = []
        for m in current_user.member_of:
            if m.project.status == 'Completed':
                completed_projects.append(m.project)

    recent_logs = ActivityLog.query.filter(
        ActivityLog.project_id.in_(my_project_ids)
    ).order_by(ActivityLog.timestamp.desc()).limit(8).all()

    return render_template('dashboard/home.html',
        p_count=proj_count,
        t_count=task_count,
        d_count=done_count,
        logs=recent_logs,
        completed_projects=completed_projects
    )


@main.route('/analytics')
@login_required
def analytics():

    stats = db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()

    chart_data = {}
    for item in stats:
        status = item[0]
        count = item[1]
        chart_data[status] = count

    return render_template('dashboard/analytics.html', chart_data=chart_data)
