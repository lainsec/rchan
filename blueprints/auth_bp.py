from flask import current_app, Blueprint, render_template, session, request, redirect, send_from_directory, flash
from database_modules import database_module, language_module, moderation_module
from flask_socketio import SocketIO, emit
from PIL import Image
from io import BytesIO
from functools import wraps
import os
import uuid
import re

auth_bp = Blueprint('auth', __name__)
socketio = SocketIO()

def has_admin_perms(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username:
            flash('You must be logged in.', 'danger')
            return redirect(request.referrer or '/')

        roles = database_module.get_user_role(username)
        if not roles or ('owner' not in roles.lower() and 'mod' not in roles.lower()):
            flash('You don’t have enough permissions.', 'danger')
            return redirect(request.referrer or '/')
        return f(*args, **kwargs)
    return decorated_function

def has_owner_perms(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username:
            flash('You must be logged in.', 'danger')
            return redirect(request.referrer or '/')

        roles = database_module.get_user_role(username)
        if not roles or 'owner' not in roles.lower():
            flash('You don’t have enough permissions.', 'danger')
            return redirect(request.referrer or '/')
        return f(*args, **kwargs)
    return decorated_function


def has_board_owner_or_admin_perms(get_board_uri_from_request):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = session.get('username')
            if not username:
                flash('You must be logged in.', 'danger')
                return redirect(request.referrer or '/')

            roles = database_module.get_user_role(username)
            is_admin = roles and ('owner' in roles.lower() or 'mod' in roles.lower())

            board_uri = get_board_uri_from_request(*args, **kwargs)
            board_owner = database_module.get_board_info(board_uri).get('board_owner')
            board_staffs = database_module.get_board_info(board_uri).get('board_staffs')

            if is_admin or username == board_owner or username in board_staffs:
                return f(*args, **kwargs)
            else:
                flash('You don’t have permission.', 'danger')
                return redirect(request.referrer or '/')
        return decorated_function
    return decorator

def allowed_file(file_storage):
    ALLOWED_EXTENSIONS = {'jpg', 'gif', 'jpeg', 'png', 'webp'}
    filename = file_storage.filename

    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    try:
        data = file_storage.read()
        file_storage.stream.seek(0)

        image = Image.open(BytesIO(data))
        image.verify()
        return True
    except Exception:
        return False

@auth_bp.route('/api/refresh_captcha', methods=['GET'])
def refresh_captcha():
    text, image = database_module.generate_captcha()
    session['captcha_text'] = text
    return {'captcha_image': image}

@auth_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'imgs', 'decoration'), 'icon.png', mimetype='image/vnd.microsoft.icon')

@auth_bp.route('/api/change_general_lang', methods=['POST'])
@has_admin_perms
def change_general_lang():
    new_lang = request.form.get('lang')
    try:
        if language_module.change_general_language(new_lang):
            flash('Language changed!', 'success')
        else:
            flash('Failed to change language.', 'danger')
    except Exception as e:
        print(e)
        flash('An error occurred.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/apply_general_captcha', methods=['POST'])
@has_admin_perms
def apply_general_captcha():
    option = request.form['generalcaptcha_option']
    if database_module.set_all_boards_captcha(option):
        flash('Captcha function set.')
    else:
        flash('Something went wrong.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/apply_captcha_on_board/<board_uri>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda board_uri: board_uri)
def apply_captcha(board_uri):
    option = request.form['boardcaptcha_option']
    if database_module.set_board_captcha(board_uri, option):
        flash('Captcha function set.')
    else:
        flash('Something went wrong.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/lock_thread/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def lock_thread(post_id):
    if database_module.lock_thread(int(post_id)):
        flash('Thread locked.')
    else:
        flash('Could not lock the thread.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/remove_board/<board_uri>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda board_uri: board_uri)
def remove_board(board_uri):
    name = session["username"]
    roles = database_module.get_user_role(name)
    if database_module.remove_board(board_uri, name, roles):
        flash('Board deleted!')
    else:
        flash('You can’t do that.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/hide_board/<board_uri>', methods=['POST'])
@has_admin_perms
def hide_board(board_uri):
    if database_module.hide_board(board_uri):
        flash('Board hidden.')
    else:
        flash('Could not hide the board.', 'danger')
    return redirect(request.referrer or '/')
        
@auth_bp.route('/api/unhide_board/<board_uri>', methods=['POST'])
@has_admin_perms
def unhide_board(board_uri):
    if database_module.unhide_board(board_uri):
        flash('Board unhidden.')
    else:
        flash('Could not unhide the board.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/report_post/<post_id>', methods=['POST'])
def report_post(post_id):
    report_manager = moderation_module.ReportManager()
    reason = request.form.get('reason')
    
    if not reason:
        flash('Please provide a reason.', 'danger')
        return redirect(request.referrer or '/')

    board_uri = database_module.get_post_board(post_id)
    if not board_uri:
        flash('Post not found.', 'danger')
        return redirect(request.referrer or '/')
        
    report_manager.add_report(reason, int(post_id), board_uri)
    flash('Report submitted!', 'success')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/resolve_report/<report_id>', methods=['POST'])
@has_admin_perms
def resolve_report(report_id):
    username = session.get('username')
    if not username:
        flash('You must be logged in.', 'danger')
        return redirect(request.referrer or '/')
    
    report_manager = moderation_module.ReportManager()
    report = report_manager.get_report(report_id)
    
    if not report:
        flash('Report not found.', 'danger')
        return redirect(request.referrer or '/')
        
    board_uri = report['board']
    
    # Check permissions
    roles = database_module.get_user_role(username)
    is_admin = roles and ('owner' in roles.lower() or 'mod' in roles.lower())
    
    board = database_module.get_board_info(board_uri)
    
    board_owner = board.get('board_owner') if board else None
    board_staffs = board.get('board_staffs', []) if board else []
    
    report_manager.resolve_reports_by_post(report['post_id'])
    flash('Reports resolved!', 'success')
        
    return redirect(request.referrer or '/')

@auth_bp.route('/api/pin_post/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def pin_post(post_id):
    if database_module.pin_post(int(post_id)):
        flash('Post pinned!')
    else:
        flash('Could not pin the post.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/delete_post/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def delete_post(post_id):
    ban_all = request.form.get('remove_all', None)
    if ban_all == 'on':
        post_info = database_module.get_post_info(int(post_id))
        poster_ip = post_info['user_ip']
        post_board = database_module.get_post_board(post_id)
        if database_module.delete_all_posts_from_user(poster_ip, post_board):
            flash('All posts deleted!')
            current_app.extensions['socketio'].emit('delete_post', {
                'type': 'Delete Post',
                'post': {'id': post_id}
            }, broadcast=True)
            return redirect(request.referrer or '/')
    if database_module.remove_post(int(post_id)):
        flash('Post deleted!')
        current_app.extensions['socketio'].emit('delete_post', {
            'type': 'Delete Post',
            'post': {'id': post_id}
        }, broadcast=True)
    else:
        flash('Could not delete post.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/delete_reply/<reply_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda reply_id: database_module.get_post_board(reply_id))
def delete_reply(reply_id):
    ban_all = request.form.get('remove_all', None)
    if ban_all == 'on':
        post_info = database_module.get_post_info(int(reply_id))
        poster_ip = post_info['user_ip']
        post_board = database_module.get_post_board(reply_id)
        if database_module.delete_all_posts_from_user(poster_ip, post_board):
            flash('All posts deleted!')
            current_app.extensions['socketio'].emit('delete_post', {
                'type': 'Delete Post',
                'post': {'id': reply_id}
            }, broadcast=True)
            return redirect(request.referrer or '/')
    if database_module.remove_reply(int(reply_id)):
        flash('Reply deleted!')
        current_app.extensions['socketio'].emit('delete_post', {
            'type': 'Delete Post',
            'post': {'id': reply_id}
        }, broadcast=True)
    else:
        flash('Could not delete reply.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/ban_user/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def ban_user(post_id):
    ban_reason = request.form['ban_reason']
    ban_from = request.form['board']
    ban_for = request.form['ban_time']
    board_uri = database_module.get_post_board(post_id)

    if ban_from == 'all':
        ban_from = None
    ban_for = None if ban_for == 'Perm' else int(ban_for)

    if database_module.check_post_exist(int(post_id)):
        post_info = database_module.get_post_info(int(post_id))
        ban_manager = moderation_module.BanManager()
        ban_manager.ban_user(post_info["user_ip"], duration_seconds=ban_for, boards=[ban_from], reason=ban_reason, moderator=session["username"])
        flash('The user has been banned!')
        current_app.extensions['socketio'].emit('ban_post', {
            'type': 'Ban Post',
            'post': {'id': post_id}
        }, broadcast=True)
    else:
        flash('An error occurred while trying to ban the user.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/move_post/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def move_post(post_id):
    new_board = request.form['new_board']
    if database_module.move_thread(int(post_id), new_board):
        flash(f'Post moved to /{new_board}/!')
        current_app.extensions['socketio'].emit('move_post', {
            'type': 'Move Post',
            'post': {'id': post_id, 'new_board': new_board}
        }, broadcast=True)
    else:
        flash('Could not move the post.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/add_board_staff/<board_uri>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda board_uri: board_uri)
def add_board_staff_route(board_uri):
    staff_username = request.form.get('username')
    if not staff_username:
        flash('No username provided.', 'danger')
        return redirect(request.referrer or '/')

    try:
        if database_module.add_board_staff(board_uri, staff_username):
            flash(f"User '{staff_username}' has been added as staff for /{board_uri}/!", 'success')
        else:
            flash('Failed to add staff member.', 'danger')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        print(e)
        flash('An unexpected error occurred.', 'danger')

    return redirect(request.referrer or '/')

@auth_bp.route('/api/remove_board_staff/<board_uri>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda board_uri: board_uri)
def remove_board_staff_route(board_uri):
    staff_username = request.form.get('username')
    if not staff_username:
        flash('No username provided.', 'danger')
        return redirect(request.referrer or '/')

    try:
        if database_module.remove_board_staff(board_uri, staff_username):
            flash(f"User '{staff_username}' has been removed from staff for /{board_uri}/!", 'success')
        else:
            flash('Failed to remove staff member.', 'danger')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('An unexpected error occurred.', 'danger')

    return redirect(request.referrer or '/')

@auth_bp.route('/api/remove_timeout/<int:timeout_id>', methods=['POST'])
@has_admin_perms
def remove_timeout(timeout_id):
    timeout_manager = moderation_module.TimeoutManager()
    timeout_manager.remove_timeout(timeout_id)
    flash('Timeout removed!', 'success')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/remove_ban/<int:ban_id>', methods=['POST'])
@has_admin_perms
def remove_ban(ban_id):
    ban_manager = moderation_module.BanManager()
    ban_manager.unban_user_by_id(ban_id)
    flash('Ban removed!', 'success')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/auth_user', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if database_module.login_user(username, password):
        session['username'] = username
        session['role'] = database_module.get_user_role(username)
        return redirect('/conta')
    flash('Invalid credentials, try again.', 'danger')
    return redirect('/conta')

@auth_bp.route('/api/register_user', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    captcha_text = request.form['captcha']
    if database_module.register_user(username, password, captcha_text, session['captcha_text']):
        return redirect('/conta')
    flash('Something went wrong, try again.')
    session['form_data'] = request.form.to_dict()
    return redirect(request.referrer or '/')

@auth_bp.route('/api/create_board', methods=['POST'])
def create_board():
    uri = request.form['uri']
    name = request.form['name']
    captcha_text = request.form['captcha']
    description = request.form['description']
    if database_module.add_new_board(uri, name, description, session['username'], captcha_text, session['captcha_text']):
        return redirect(f'/{uri}')
    flash('Something went wrong, try again.')
    session['form_data'] = request.form.to_dict()
    return redirect(request.referrer or '/')

@auth_bp.route('/api/upload_banner', methods=['POST'])
@has_board_owner_or_admin_perms(lambda: request.form.get('board_uri'))
def upload_banner():
    board_uri = request.form['board_uri']
    file = request.files.get('imageUpload')

    if not file or file.filename == '':
        flash('No file uploaded.', 'danger')
        return redirect(request.referrer or '/')
        
    # Sanitize board_uri to prevent LFI
    if not re.match(r'^[a-zA-Z0-9_]+$', board_uri):
        flash('Invalid board URI.', 'danger')
        return redirect(request.referrer or '/')

    if allowed_file(file):
        directory = os.path.join(f'./static/imgs/banners/{board_uri}')
        os.makedirs(directory, exist_ok=True)
        
        # Generate random filename
        ext = os.path.splitext(file.filename)[1].lower()
        new_filename = f"{uuid.uuid4().hex}{ext}"
        
        file.save(os.path.join(directory, new_filename))
        flash('Banner uploaded!')
    else:
        flash('Invalid image file.', 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/delete_banner', methods=['POST'])
def delete_banner():
    if 'username' not in session:
        return redirect(url_for('boards.main_page'))
    
    username = session['username']
    board_uri = request.form.get('board_uri')
    banner_filename = request.form.get('banner_filename')
    
    if not board_uri or not banner_filename:
        flash('Invalid request')
        return redirect(request.referrer)
        
    board_info = database_module.get_board_info(board_uri)
    if not board_info:
        return redirect(request.referrer)
        
    roles = database_module.get_user_role(username)
    user_roles = roles.lower() if roles else ''
    
    is_moderator = 'mod' in user_roles or 'owner' in user_roles
    is_board_staff = username in board_info.get('board_staffs', [])
    is_board_owner = username == board_info.get('board_owner')
    
    if is_board_owner or is_moderator or is_board_staff:
        if database_module.delete_board_banner(board_uri, banner_filename):
            flash('Banner deleted successfully')
        else:
            flash('Error deleting banner')
    else:
        flash('You do not have permission to delete banners')
        
    return redirect(request.referrer)

@auth_bp.route('/api/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        flash('You has been disconnected.', 'info')
    return redirect('/')

@auth_bp.route('/api/change_user_role', methods=['POST'])
@has_owner_perms
def change_user_role():
    target_username = request.form.get('username')
    new_role = request.form.get('role')
    
    if not target_username or new_role not in ['mod', 'user', 'owner']: # Basic validation
         flash('Invalid request parameters.', 'danger')
         return redirect(request.referrer or '/conta/users')
         
    # Adjust role string for DB
    if new_role == 'user':
        new_role = ''
        
    if database_module.update_user_role(target_username, new_role):
        flash(f"User {target_username} role updated to {new_role if new_role else 'User'}.", 'success')
    else:
        flash('Failed to update user role.', 'danger')
        
    return redirect(request.referrer or '/conta/users')

