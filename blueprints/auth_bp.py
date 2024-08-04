from flask import current_app, Blueprint, render_template, session, request, redirect,send_from_directory
from database_modules import database_module
from config import config_module
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.before_request
def before_request():
    return config_module.check_banned_user()

@auth_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'imgs','decoration'), 'icon.png', mimetype='image/vnd.microsoft.icon')
