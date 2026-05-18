from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app import socketio, db
from app.models import Message, DirectMessage, Project, User, ProjectMember
from flask_socketio import emit, join_room


chat_bp = Blueprint('chat', __name__)


def get_projects():
    if current_user.role == 'Admin':
        return Project.query.filter_by(created_by=current_user.id).all()
    else:
        result = []
        for membership in current_user.member_of:
            result.append(membership.project)
        return result


def get_teammates():

    teammate_ids = set()

    if current_user.role == 'Admin':
        my_projects = Project.query.filter_by(created_by=current_user.id).all()
        for p in my_projects:
            for pm in p.members:
                if pm.user_id != current_user.id:
                    teammate_ids.add(pm.user_id)
    else:
        for m in current_user.member_of:
            for pm in m.project.members:
                if pm.user_id != current_user.id:
                    teammate_ids.add(pm.user_id)
            if m.project.created_by != current_user.id:
                teammate_ids.add(m.project.created_by)

    if len(teammate_ids) == 0:
        return []

    teammates = User.query.filter(User.id.in_(teammate_ids)).all()
    return teammates


@chat_bp.route('/messages')
@login_required
def index():
    projects = get_projects()
    teammates = get_teammates()
    return render_template('chat/chat_home.html',
        projects=projects,
        teammates=teammates,
        active_type=None,
        active_id=None,
        active_project=None,
        dm_user=None,
        group_messages=[],
        dm_messages=[]
    )


@chat_bp.route('/messages/group/<int:project_id>')
@login_required
def group(project_id):

    project = Project.query.get_or_404(project_id)
    projects = get_projects()
    teammates = get_teammates()

    msgs = Message.query.filter_by(project_id=project_id).order_by(Message.timestamp.asc()).limit(100).all()

    return render_template('chat/chat_home.html',
        projects=projects,
        teammates=teammates,
        active_type='group',
        active_id=project_id,
        active_project=project,
        dm_user=None,
        group_messages=msgs,
        dm_messages=[]
    )


@chat_bp.route('/messages/group/<int:project_id>/send', methods=['POST'])
@login_required
def send_group(project_id):

    content = request.form.get('content', '').strip()

    if content != '':
        msg = Message()
        msg.sender_id = current_user.id
        msg.project_id = project_id
        msg.content = content
        db.session.add(msg)
        db.session.commit()

    return redirect(url_for('chat.group', project_id=project_id))


@chat_bp.route('/messages/dm/<int:user_id>')
@login_required
def dm(user_id):

    other = User.query.get_or_404(user_id)
    projects = get_projects()
    teammates = get_teammates()

    msgs = DirectMessage.query.filter(
        db.or_(
            db.and_(DirectMessage.sender_id == current_user.id, DirectMessage.receiver_id == user_id),
            db.and_(DirectMessage.sender_id == user_id, DirectMessage.receiver_id == current_user.id)
        )
    ).order_by(DirectMessage.timestamp.asc()).limit(100).all()

    return render_template('chat/chat_home.html',
        projects=projects,
        teammates=teammates,
        active_type='dm',
        active_id=user_id,
        active_project=None,
        dm_user=other,
        group_messages=[],
        dm_messages=msgs
    )


@chat_bp.route('/messages/dm/<int:user_id>/send', methods=['POST'])
@login_required
def send_dm(user_id):

    content = request.form.get('content', '')
    content = content.strip()

    if content != '':
        msg = DirectMessage()
        msg.sender_id = current_user.id
        msg.receiver_id = user_id
        msg.content = content
        db.session.add(msg)
        db.session.commit()

    return redirect(url_for('chat.dm', user_id=user_id))


@socketio.on('join')
def handle_join(data):
    project_id = data['project_id']
    room_name = "project_" + str(project_id)
    join_room(room_name)


@socketio.on('send_msg')
def handle_msg(data):
    project_id = data['project_id']
    message_text = data['message']

    msg = Message()
    msg.sender_id = current_user.id
    msg.project_id = project_id
    msg.content = message_text
    db.session.add(msg)
    db.session.commit()

    formatted_time = msg.timestamp.strftime('%H:%M')

    room_name = "project_" + str(project_id)
    emit('new_msg', {
        'user': current_user.full_name,
        'text': message_text,
        'time': formatted_time
    }, room=room_name)
