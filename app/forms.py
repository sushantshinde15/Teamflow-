from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):

    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Company Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('Admin', 'Admin'), ('Member', 'Member')])
    submit = SubmitField('Join TeamFlow')

    # wtforms calls this automatically when form is validated
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    deadline = DateField('Target Deadline', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical')
    ])
    submit = SubmitField('Launch Project')


# task form - assigned_to choices get set in the route not here
class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired()])
    description = TextAreaField('Task Details')
    assigned_to = SelectField('Assign To', coerce=int)
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ])
    deadline = DateField('Due Date', validators=[DataRequired()])
    submit = SubmitField('Assign Task')


class ReportForm(FlaskForm):
    summary = TextAreaField('What did you achieve?', validators=[DataRequired()])
    changes_made = TextAreaField('Specific changes')
    time_taken = StringField('Estimated time spent (hrs)')
    submit = SubmitField('Submit Final Report')
