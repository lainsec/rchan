from flask import current_app, Blueprint, render_template, session, request, redirect, send_from_directory, flash
from database_modules import database_module, language_module, moderation_module
from flask_socketio import SocketIO, emit
import os

# Blueprint register
auth_bp = Blueprint('auth', __name__)
socketio = SocketIO()

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'gif', 'jpeg', 'png', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'imgs', 'decoration'), 'icon.png', mimetype='image/vnd.microsoft.icon')

@auth_bp.route('/change_general_lang', methods=['POST'])
def change_general_lang():
    new_lang = request.form.get('lang')
    if 'username' in session:
        roles = database_module.get_user_role(session["username"])
        if 'owner' in roles.lower():
            try:
                if language_module.change_general_language(new_lang):
                    flash('Language changed!')
                    return redirect(request.referrer)
            except Exception as e:
                print(e)
        flash('You cant do it!')
    else:
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
        flash('Something went wrong, try again.')
    return redirect(request.referrer)

@auth_bp.route('/create_board', methods=['POST'])
def create_board():
    if request.method == 'POST':
        uri = request.form['uri']
        name = request.form['name']
        captcha_text = request.form['captcha']
        description = request.form['description']

        if database_module.add_new_board(uri, name, description, session['username'], captcha_text, session['captcha_text']):
            return redirect(f'/{uri}')
        flash('Something went wrong, try again.')
        return redirect(request.referrer)
    return redirect('/')

@auth_bp.route('/apply_general_captcha', methods=['POST'])
def apply_general_captcha():
    if request.method == 'POST' and 'username' in session:
        option = request.form['generalcaptcha_option']
        roles = database_module.get_user_role(session["username"])
        if 'owner' in roles.lower() or 'mod' in roles.lower():
            if database_module.set_all_boards_captcha(option):
                flash('Captcha function setted.')
            else:
                flash('Something went wrong, try again.')
        else:
            flash('Not enough permissions.')
    return redirect(request.referrer or '/')

@auth_bp.route('/lock_thread/<post_id>', methods=['POST'])
def lock_thread(post_id):
    if request.method == 'POST' and 'username' in session:
        board_uri = database_module.get_post_board(post_id)
        board_owner = database_module.get_board_info(board_uri)["board_owner"]
        roles = database_module.get_user_role(session["username"])
        if 'owner' in roles.lower() or 'mod' in roles.lower() or session["username"] == board_owner:
            if database_module.lock_thread(int(post_id)):
                flash('Thread locked.')
            else:
                flash('You cant do it.')
        else:
            flash('You are not the board owner.')
    return redirect(request.referrer or '/')

@auth_bp.route('/remove_board/<board_uri>', methods=['POST'])
def remove_board(board_uri):
    if request.method == 'POST' and 'username' in session:
        name = session["username"]
        roles = database_module.get_user_role(session["username"])
        if database_module.remove_board(board_uri, name, roles):
            flash('Board deleted!')
        else:
            flash('You cant do it!')
    return redirect(request.referrer or '/')

@auth_bp.route('/upload_banner', methods=['POST'])
def upload_banner():
    if 'username' not in session:
        flash('You must be logged in.')
        return redirect(request.referrer)
    
    board_uri = request.form['board_uri']
    board_info = database_module.get_board_info(board_uri)
    if session['username'] != board_info.get('board_owner'):
        flash('You are not the board owner.')
        return redirect(request.referrer)
    
    if 'imageUpload' not in request.files or request.files['imageUpload'].filename == '':
        return redirect(request.referrer)
    
    file = request.files['imageUpload']
    if file and allowed_file(file.filename):
        directory = os.path.join(f'./static/imgs/banners/{board_uri}')
        os.makedirs(directory, exist_ok=True)
        file.save(os.path.join(directory, file.filename))
    return redirect(request.referrer)

@auth_bp.route('/pin_post/<post_id>', methods=['POST'])
def pin_post(post_id):
    if 'username' not in session:
        flash('You must be logged in.')
        return redirect(request.referrer)
    
    board_uri = database_module.get_post_board(post_id)
    board_owner = database_module.get_board_info(board_uri)["board_owner"]
    roles = database_module.get_user_role(session["username"])
    if 'owner' in roles.lower() or 'mod' in roles.lower() or session["username"] == board_owner:
        if database_module.pin_post(int(post_id)):
            flash('Post pinned!')
        else:
            flash('You are not the board owner.')
    return redirect(request.referrer)

@auth_bp.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    if 'username' not in session:
        flash('You must be logged in.')
        return redirect(request.referrer)
    
    board_uri = database_module.get_post_board(post_id)
    board_owner = database_module.get_board_info(board_uri)["board_owner"]
    roles = database_module.get_user_role(session["username"])
    if 'owner' in roles.lower() or 'mod' in roles.lower() or session["username"] == board_owner:
        if database_module.remove_post(int(post_id)):
            flash('Post deleted!')
            current_app.extensions['socketio'].emit('delete_post', {
            'type': 'Delete Post',
            'post': {
                'id': post_id,
            }
        }, broadcast=True)
        else:
            flash('You are not the board owner.')
    return redirect(request.referrer)

@auth_bp.route('/delete_reply/<reply_id>', methods=['POST'])
def delete_reply(reply_id):
    if 'username' not in session:
        flash('You must be logged in.')
        return redirect(request.referrer)
    
    board_uri = database_module.get_post_board(reply_id)
    board_owner = database_module.get_board_info(board_uri)["board_owner"]
    roles = database_module.get_user_role(session["username"])
    if 'owner' in roles.lower() or 'mod' in roles.lower() or session["username"] == board_owner:
        if database_module.remove_reply(int(reply_id)):
            flash('Reply deleted!')
            current_app.extensions['socketio'].emit('delete_post', {
            'type': 'Delete Post',
            'post': {
                'id': reply_id,
            }
        }, broadcast=True)
        else:
            flash('You are not the board owner.')
    return redirect(request.referrer)

@auth_bp.route('/ban_user/<post_id>', methods=['POST'])
def ban_user(post_id):
    if 'username' not in session:
        flash('You must be logged in.')
        return redirect(request.referrer)
    
    board_uri = database_module.get_post_board(post_id)
    board_owner = database_module.get_board_info(board_uri)["board_owner"]
    roles = database_module.get_user_role(session["username"])
    if 'owner' in roles.lower() or 'mod' in roles.lower():
        if database_module.check_post_exist(int(post_id)):
            ban_manager = moderation_module.BanManager()
            ban_manager.ban_user(database_module.get_post_info(int(post_id))["user_ip"], duration_seconds=None, boards=None, reason="No reason.", moderator=session["username"])
            flash('The user has been banned!')
            current_app.extensions['socketio'].emit('ban_post', {
            'type': 'Ban Post',
            'post': {
                'id': post_id,
            }
            }, broadcast=True)
            return redirect(request.referrer)
        else:
            flash('An error ocurred while trying to ban the user.')
    elif session["username"] == board_owner:
        if database_module.check_post_exist(int(post_id)):
            ban_manager = moderation_module.BanManager()
            ban_manager.ban_user(database_module.get_post_info(int(post_id))["user_ip"], duration_seconds=None, boards=[board_uri], reason="No reason.", moderator=session["username"])
            flash('The user has been banned!')
            current_app.extensions['socketio'].emit('ban_post', {
            'type': 'Ban Post',
            'post': {
                'id': post_id,
            }
            }, broadcast=True)
            return redirect(request.referrer)
        else:
            flash('An error ocurred while trying to ban the user.')
    flash("You don't have permission to ban.")
    return redirect(request.referrer)

@auth_bp.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        flash('You has been disconnected.', 'info')
    return redirect('/')
