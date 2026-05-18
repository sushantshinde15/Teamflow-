import os

from dotenv import load_dotenv
load_dotenv()

class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY')
    if SECRET_KEY is None:
        SECRET_KEY = 'teamflow-secret-key-2024'

    # using sqlite for now, might change later
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'static', 'uploads')

    # 10mb max
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    @staticmethod
    def init_app(app):
        folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'static', 'uploads')
        if not os.path.exists(folder):
            os.makedirs(folder)
