from flask import current_app, Blueprint, render_template, session, request, redirect, send_from_directory, flash
from database_modules import database_module
from database_modules import language_module
from config import config_module
import os

auth_bp = Blueprint('auth', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'gif', 'jpeg', 'png', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.before_request
def before_request():
    return config_module.check_banned_user()

@auth_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'imgs', 'decoration'), 'icon.png', mimetype='image/vnd.microsoft.icon')

@auth_bp.route('/change_general_lang', methods=['POST'])
def change_general_lang():
    new_lang = request.form.get('lang')
    if 'username' in session:
        roles = database_module.get_user_role(session["username"])
        if 'owner' in roles.lower() :
            if language_module.change_general_language(new_lang):
                flash('Language changed!')
                return redirect(request.referrer)
            flash('You cant do it!')
            return redirect(request.referrer)
        flash('You cant do it!')
        return redirect(request.referrer)
    flash('You cant do it!')
    return redirect(request.referrer)

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
            flash('Invalid credentials, try again.', 'danger')

    return redirect('/conta')

@auth_bp.route('/register_user', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        captcha_text = request.form['captcha']

        if database_module.register_user(username, password, captcha_text, session['captcha_text']):
            return redirect('/conta')
        else:
            flash('Something went wrong, try again.')

    return redirect('/conta')

@auth_bp.route('/create_board', methods=['POST'])
def create_board():
    if request.method == 'POST':
        uri = request.form['uri']
        name = request.form['name']
        captcha_text = request.form['captcha']
        description = request.form['description']

        if database_module.add_new_board(uri, name, description, session['username'], captcha_text, session['captcha_text']):
            return redirect(f'/{uri}')
        else:
            flash('Something went wrong, try again.')

    return redirect('/')

@auth_bp.route('/apply_general_captcha', methods=['POST'])
def apply_general_captcha():
    if request.method == 'POST':
        option = request.form['generalcaptcha_option']
        if 'username' in session:
            roles = database_module.get_user_role(session["username"])
            if 'owner' in roles.lower() or 'mod' in roles.lower():
                if database_module.set_all_boards_captcha(option):
                    flash('Captcha function setted.')
                    return redirect(request.referrer)
                else:
                    flash('Something went wrong, try again.')
                    return redirect(request.referrer)
    return redirect('/')

@auth_bp.route('/lock_thread/<post_id>', methods=['POST'])
def lock_thread(post_id):
    if request.method == 'POST':
        board_owner = request.form['board_owner']
        if 'username' in session:
            roles = database_module.get_user_role(session["username"])
            if 'owner' in roles.lower() or 'mod' in roles.lower() or session["username"] == board_owner:
                if database_module.lock_thread(int(post_id)):
                    flash('Thread locked.')
                    return redirect(request.referrer)
                else:
                    flash('You cant do it.')
                    return redirect(request.referrer)
    return redirect('/')

@auth_bp.route('/remove_board/<board_uri>', methods=['POST'])
def remove_board(board_uri):
    if request.method == 'POST':
        if 'username' in session:
            name = session["username"]
            if database_module.remove_board(board_uri, name):
                flash('Board deleted!')
                return redirect(request.referrer)
            else:
                flash('You cant do it!')
                return redirect(request.referrer)

    return redirect('/')

@auth_bp.route('/upload_banner', methods=['POST'])
def upload_banner():
    if 'imageUpload' not in request.files:
        return redirect(request.referrer)
    file = request.files['imageUpload']
    if file.filename == '':
        return redirect(request.referrer)
    if file and allowed_file(file.filename):
        board_uri = request.form['board_uri']
        directory = os.path.join(f'./static/imgs/banners/{board_uri}')
        os.makedirs(directory, exist_ok=True)  
        file.save(os.path.join(directory, file.filename))
        return redirect(request.referrer)
    return redirect(request.referrer)

@auth_bp.route('/pin_post/<post_id>', methods=['POST'])
def pin_post(post_id):
    board_owner = request.form['board_owner']
    post_id = int(post_id)
    if 'username' in session:
        if session["role"] == 'mod' or session["username"] == board_owner:
            if database_module.pin_post(post_id):
                flash('Post pinned!')
                return redirect(request.referrer)

@auth_bp.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    board_owner = request.form['board_owner']
    post_id = int(post_id)
    if 'username' in session:
        if session["role"] == 'mod' or session["username"] == board_owner:
            if database_module.remove_post(post_id):
                flash('Post deleted!')
                return redirect(request.referrer)

@auth_bp.route('/delete_reply/<reply_id>', methods=['POST'])
def delete_reply(reply_id):
    board_owner = request.form['board_owner']
    if 'username' in session:
        if session["role"] == 'mod' or session["username"] == board_owner:
            reply_id = int(reply_id)
            if database_module.remove_reply(reply_id):
                flash('Reply deleted!')
                return redirect(request.referrer)

@auth_bp.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        flash('You has been disconnected.', 'info')
        return redirect('/')
    else:
        return redirect('/conta')
