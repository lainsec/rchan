from flask import session, request
from database_modules import database_module

def check_banned_user():
    session["user_ip"] = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For')
    if database_module.check_banned_user(session["user_ip"]):
        return render_template('utils/banned.html')
