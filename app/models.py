from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='Member')  # Admin or Member
    profile_image = db.Column(db.String(100), default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_tasks = db.relationship('Task', backref='assignee', lazy=True, foreign_keys='Task.assigned_to')
    member_of = db.relationship('ProjectMember', backref='user', lazy=True)
    messages_sent = db.relationship('Message', backref='sender', lazy=True)
    task_files = db.relationship('TaskFile', backref='uploader', lazy=True)
    reports = db.relationship('TaskReport', backref='member', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        result = check_password_hash(self.password_hash, password)
        return result


class Project(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    deadline = db.Column(db.Date)
    priority = db.Column(db.String(20))  # Low, Medium, High, Critical
    status = db.Column(db.String(20), default='Active')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('ProjectMember', backref='project', cascade="all, delete", lazy=True)
    tasks = db.relationship('Task', backref='project', cascade="all, delete", lazy=True)
    messages = db.relationship('Message', backref='project', cascade="all, delete", lazy=True)


# joins users to projects
class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    priority = db.Column(db.String(20))
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='To Do')  # To Do, In Progress, Review, Completed, Overdue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship('TaskFile', backref='task', cascade="all, delete", lazy=True)
    report = db.relationship('TaskReport', backref='task', uselist=False, cascade="all, delete")  # only one report per task


class TaskFile(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)       # random name saved on disk
    original_name = db.Column(db.String(200), nullable=False)  # original filename from user
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class TaskReport(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    member_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    summary = db.Column(db.Text, nullable=False)
    changes_made = db.Column(db.Text)
    files_modified = db.Column(db.String(200))
    time_taken = db.Column(db.String(50))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class DirectMessage(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # two fks pointing to same table so flask gets confused without this
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_dms')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_dms')


class ActivityLog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
