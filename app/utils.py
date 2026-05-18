from functools import wraps
from flask import abort
from flask_login import current_user
import secrets
import os


# blocks access if user isnt an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if current_user.role != 'Admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def save_picture(form_picture, upload_folder):

    # random name so files dont overwrite each other
    random_hex = secrets.token_hex(8)
    original_filename = form_picture.filename
    split_name = os.path.splitext(original_filename)
    f_ext = split_name[1]
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(upload_folder, picture_fn)
    form_picture.save(picture_path)

    return picture_fn
