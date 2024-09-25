from flask import session, request
from database_modules import database_module

def check_banned_user():
    session["user_ip"] = request.remote_addr
    if database_module.check_banned_user(session["user_ip"]):
        return render_template('utils/banned.html')
