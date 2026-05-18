from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import date

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

socketio = SocketIO()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)

    # need today's date in templates to check deadlines
    @app.context_processor
    def inject_today():
        todays_date = date.today()
        return dict(today=todays_date)

    # imports here to avoid circular imports
    from app.routes.auth import auth
    from app.routes.projects import projects
    from app.routes.tasks import tasks
    from app.routes.main import main
    from app.routes.chat import chat_bp

    app.register_blueprint(auth)
    app.register_blueprint(projects)
    app.register_blueprint(tasks)
    app.register_blueprint(main)
    app.register_blueprint(chat_bp)

    return app
