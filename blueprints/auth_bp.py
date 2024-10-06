from flask import current_app, Blueprint, render_template, session, request, redirect, send_from_directory, flash
from database_modules import database_module
from config import config_module
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.before_request
def before_request():
    return config_module.check_banned_user()

@auth_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'imgs', 'decoration'), 'icon.png', mimetype='image/vnd.microsoft.icon')

@auth_bp.route('/auth_user', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if database_module.login_user(username, password):
            session['username'] = username
            session['role'] = database_module.get_user_role(username) 
            return redirect('/conta')
        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')

    return render_template('login.html')

@auth_bp.route('/register_user', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if database_module.register_user(username, password):
            return redirect('/conta')
        else:
            flash('cu')

    return render_template('login.html')

@auth_bp.route('/create_board', methods=['POST'])
def create_board():
    if request.method == 'POST':
        uri = request.form['uri']
        name = request.form['name']
        description = request.form['description']

        if database_module.add_new_board(uri, name, description, session['username']):
            return redirect(f'/{uri}')
        else:
            flash('ocorreu um erro ai, fdp!')

    return redirect('/')

@auth_bp.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        flash('Você foi desconectado.', 'info')
        return redirect('/')
    else:
        return redirect('/conta')
