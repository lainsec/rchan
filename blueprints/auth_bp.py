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

def get_lang():
    return language_module.get_user_lang('default')
socketio = SocketIO()

def has_admin_perms(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username:
            lang = get_lang()
            flash(lang["flash-login-required"], 'danger')
            return redirect(request.referrer or '/')

        roles = database_module.get_user_role(username)
        if not roles or ('owner' not in roles.lower() and 'mod' not in roles.lower()):
            lang = get_lang()
            flash(lang["flash-not-enough-permissions"], 'danger')
            return redirect(request.referrer or '/')
        return f(*args, **kwargs)
    return decorated_function

def has_owner_perms(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username:
            lang = get_lang()
            flash(lang["flash-login-required"], 'danger')
            return redirect(request.referrer or '/')

        roles = database_module.get_user_role(username)
        if not roles or 'owner' not in roles.lower():
            lang = get_lang()
            flash(lang["flash-not-enough-permissions"], 'danger')
            return redirect(request.referrer or '/')
        return f(*args, **kwargs)
    return decorated_function


def has_board_owner_or_admin_perms(get_board_uri_from_request):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = session.get('username')
            if not username:
                lang = get_lang()
                flash(lang["flash-login-required"], 'danger')
                return redirect(request.referrer or '/')

            roles = database_module.get_user_role(username)
            is_admin = roles and ('owner' in roles.lower() or 'mod' in roles.lower())

            board_uri = get_board_uri_from_request(*args, **kwargs)
            board_owner = database_module.get_board_info(board_uri).get('board_owner')
            board_staffs = database_module.get_board_info(board_uri).get('board_staffs')

            if is_admin or username == board_owner or username in board_staffs:
                return f(*args, **kwargs)
            lang = get_lang()
            flash(lang["flash-no-permission"], 'danger')
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

@auth_bp.route('/api/get_post_info', methods=['GET'])
def get_post_info():
    post_id = request.args.get('post_id')
    if not post_id:
        return {'error': 'Post ID is required'}, 400

    post_info = database_module.get_post_info(post_id)
    if post_info:
        return post_info
    else:
        return {'error': 'Post not found'}, 404

@auth_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'imgs', 'decoration'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@auth_bp.route('/api/change_news', methods=['POST'])
@has_admin_perms
def change_news():
    news = request.form.get('news')
    config_manager = moderation_module.ChanConfigManager()
    config_manager.update_config(index_news=news)
    lang = get_lang()
    flash(lang["flash-news-updated"], 'success')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/toggle_free_board_creation', methods=['POST'])
@has_admin_perms
def toggle_free_board_creation():
    config_manager = moderation_module.ChanConfigManager()
    option = request.form.get('free_board_creation_option')
    lang = get_lang()
    if option:
        new_value = True if option == 'enable' else False
        config_manager.update_config(free_board_creation=new_value)
        if new_value:
            flash(lang["flash-free-board-creation-enabled"], 'success')
        else:
            flash(lang["flash-free-board-creation-disabled"], 'success')
    else:
        chan_config = config_manager.get_config()
        new_value = not chan_config['free_board_creation']
        config_manager.update_config(free_board_creation=new_value)
        flash(lang["flash-free-board-creation-toggled"], 'success')
        
    return redirect(request.referrer or '/')


@auth_bp.route('/api/toggle_sidebar_layout', methods=['POST'])
@has_admin_perms
def toggle_sidebar_layout():
    config_manager = moderation_module.ChanConfigManager()
    
    option = request.form.get('sidebar_option')
    
    lang = get_lang()
    if option:
        new_value = True if option == 'enable' else False
        config_manager.update_config(sidebar_enabled=new_value)
        if new_value:
            flash(lang["flash-sidebar-layout-enabled"], 'success')
        else:
            flash(lang["flash-sidebar-layout-disabled"], 'success')
    else:
        chan_config = config_manager.get_config()
        current = bool(chan_config.get('sidebar_enabled', 0))
        new_value = not current
        config_manager.update_config(sidebar_enabled=new_value)
        flash(lang["flash-sidebar-layout-toggled"], 'success')
        
    return redirect(request.referrer or '/')

@auth_bp.route('/api/change_general_lang', methods=['POST'])
@has_admin_perms
def change_general_lang():
    new_lang = request.form.get('lang')
    try:
        lang = get_lang()
        if language_module.change_general_language(new_lang):
            flash(lang["flash-language-changed"], 'success')
        else:
            flash(lang["flash-language-change-failed"], 'danger')
    except Exception as e:
        print(e)
        lang = get_lang()
        flash(lang["flash-generic-error"], 'danger')
    return redirect(request.referrer or '/')


@auth_bp.route('/api/update_chan_defaults', methods=['POST'])
@has_admin_perms
def update_chan_defaults():
    config_manager = moderation_module.ChanConfigManager()
    default_name = request.form.get('default_poster_name', '')
    max_pages_raw = request.form.get('max_pages_per_board', '').strip()
    posts_per_page_raw = request.form.get('posts_per_page', '').strip()

    max_pages_value = None
    if max_pages_raw != '':
        try:
            max_pages_value = int(max_pages_raw)
        except (TypeError, ValueError):
            max_pages_value = 0

    posts_per_page_value = None
    if posts_per_page_raw != '':
        try:
            posts_per_page_value = int(posts_per_page_raw)
        except (TypeError, ValueError):
            posts_per_page_value = 6

    config_manager.update_config(
        default_poster_name=default_name,
        max_pages_per_board=max_pages_value,
        posts_per_page=posts_per_page_value
    )

    lang = get_lang()
    flash(lang["flash-global-defaults-updated"], 'success')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/apply_general_captcha', methods=['POST'])
@has_admin_perms
def apply_general_captcha():
    option = request.form['generalcaptcha_option']
    lang = get_lang()
    if database_module.set_all_boards_captcha(option):
        flash(lang["flash-captcha-set"])
    else:
        flash(lang["flash-something-went-wrong"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/apply_captcha_on_board/<board_uri>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda board_uri: board_uri)
def apply_captcha(board_uri):
    option = request.form['boardcaptcha_option']
    lang = get_lang()
    if database_module.set_board_captcha(board_uri, option):
        flash(lang["flash-captcha-set"])
    else:
        flash(lang["flash-something-went-wrong"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/lock_thread/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def lock_thread(post_id):
    lang = get_lang()
    if database_module.lock_thread(int(post_id)):
        flash(lang["flash-thread-locked"])
    else:
        flash(lang["flash-thread-lock-failed"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/remove_board/<board_uri>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda board_uri: board_uri)
def remove_board(board_uri):
    name = session["username"]
    roles = database_module.get_user_role(name)
    lang = get_lang()
    if database_module.remove_board(board_uri, name, roles):
        flash(lang["flash-board-deleted"])
    else:
        flash(lang["flash-action-not-allowed"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/hide_board/<board_uri>', methods=['POST'])
@has_admin_perms
def hide_board(board_uri):
    lang = get_lang()
    if database_module.hide_board(board_uri):
        flash(lang["flash-board-hidden"])
    else:
        flash(lang["flash-board-hide-failed"], 'danger')
    return redirect(request.referrer or '/')
        
@auth_bp.route('/api/unhide_board/<board_uri>', methods=['POST'])
@has_admin_perms
def unhide_board(board_uri):
    lang = get_lang()
    if database_module.unhide_board(board_uri):
        flash(lang["flash-board-unhidden"])
    else:
        flash(lang["flash-board-unhide-failed"], 'danger')
    return redirect(request.referrer or '/')
@auth_bp.route('/api/word_filters/add', methods=['POST'])
@has_admin_perms
def add_word_filter():
    word = request.form.get('word', '').strip()
    replacement = request.form.get('filter', '')
    mode = request.form.get('mode', 'word')
    manager = moderation_module.WordFilterManager()
    lang = get_lang()
    if manager.add_filter(word, replacement, mode):
        flash(lang["flash-word-filter-added"], 'success')
    else:
        flash(lang["flash-word-filter-add-failed"], 'danger')
    return redirect(request.referrer or '/conta/word_filters')
@auth_bp.route('/api/word_filters/delete/<int:filter_id>', methods=['POST'])
@has_admin_perms
def delete_word_filter(filter_id):
    manager = moderation_module.WordFilterManager()
    lang = get_lang()
    if manager.delete_filter(filter_id):
        flash(lang["flash-word-filter-removed"], 'success')
    else:
        flash(lang["flash-word-filter-remove-failed"], 'danger')
    return redirect(request.referrer or '/conta/word_filters')

@auth_bp.route('/api/report_post/<post_id>', methods=['POST'])
def report_post(post_id):
    report_manager = moderation_module.ReportManager()
    reason = request.form.get('reason')
    
    lang = get_lang()
    if not reason:
        flash(lang["flash-report-reason-required"], 'danger')
        return redirect(request.referrer or '/')

    board_uri = database_module.get_post_board(post_id)
    if not board_uri:
        flash(lang["flash-post-not-found"], 'danger')
        return redirect(request.referrer or '/')
        
    report_manager.add_report(reason, int(post_id), board_uri)
    flash(lang["flash-report-submitted"], 'success')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/resolve_report/<report_id>', methods=['POST'])
@has_admin_perms
def resolve_report(report_id):
    username = session.get('username')
    lang = get_lang()
    if not username:
        flash(lang["flash-login-required"], 'danger')
        return redirect(request.referrer or '/')
    
    report_manager = moderation_module.ReportManager()
    report = report_manager.get_report(report_id)
    
    if not report:
        flash(lang["flash-post-not-found"], 'danger')
        return redirect(request.referrer or '/')
        
    board_uri = report['board']
    
    # Check permissions
    roles = database_module.get_user_role(username)
    is_admin = roles and ('owner' in roles.lower() or 'mod' in roles.lower())
    
    board = database_module.get_board_info(board_uri)
    
    board_owner = board.get('board_owner') if board else None
    board_staffs = board.get('board_staffs', []) if board else []
    
    report_manager.resolve_reports_by_post(report['post_id'])
    flash(lang["flash-reports-resolved"], 'success')
        
    return redirect(request.referrer or '/')

@auth_bp.route('/api/approve_media/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def approve_media(post_id):
    is_reply = request.form.get('is_reply', 'false') == 'true'
    lang = get_lang()
    if database_module.approve_media(int(post_id), is_reply):
        flash(lang["flash-media-approved"])
    else:
        flash(lang["flash-media-approve-failed"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/pin_post/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def pin_post(post_id):
    lang = get_lang()
    if database_module.pin_post(int(post_id)):
        flash(lang["flash-post-pinned"])
    else:
        flash(lang["flash-post-pin-failed"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/delete_post/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def delete_post(post_id):
    ban_all = request.form.get('remove_all', None)
    if ban_all == 'on':
        post_info = database_module.get_post_info(int(post_id))
        poster_ip = database_module.get_post_ip(int(post_id))
        post_board = database_module.get_post_board(post_id)
        lang = get_lang()
        if database_module.delete_all_posts_from_user(poster_ip, post_board):
            flash(lang["flash-all-posts-deleted"])
            current_app.extensions['socketio'].emit('delete_post', {
                'type': 'Delete Post',
                'post': {'id': post_id}
            }, broadcast=True)
            return redirect(request.referrer or '/')
    lang = get_lang()
    if database_module.remove_post(int(post_id)):
        flash(lang["flash-post-deleted"])
        current_app.extensions['socketio'].emit('delete_post', {
            'type': 'Delete Post',
            'post': {'id': post_id}
        }, broadcast=True)
    else:
        flash(lang["flash-post-delete-failed"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/delete_reply/<reply_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda reply_id: database_module.get_post_board(reply_id))
def delete_reply(reply_id):
    ban_all = request.form.get('remove_all', None)
    if ban_all == 'on':
        post_info = database_module.get_post_info(int(reply_id))
        poster_ip = post_info['user_ip']
        post_board = database_module.get_post_board(reply_id)
        lang = get_lang()
        if database_module.delete_all_posts_from_user(poster_ip, post_board):
            flash(lang["flash-all-posts-deleted"])
            current_app.extensions['socketio'].emit('delete_post', {
                'type': 'Delete Post',
                'post': {'id': reply_id}
            }, broadcast=True)
            return redirect(request.referrer or '/')
    lang = get_lang()
    if database_module.remove_reply(int(reply_id)):
        flash(lang["flash-reply-deleted"])
        current_app.extensions['socketio'].emit('delete_post', {
            'type': 'Delete Post',
            'post': {'id': reply_id}
        }, broadcast=True)
    else:
        flash(lang["flash-reply-delete-failed"], 'danger')
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

    lang = get_lang()
    if database_module.check_post_exist(int(post_id)):
        post_info = database_module.get_post_info(int(post_id))
        post_ip = database_module.get_post_ip(int(post_id))
        ban_manager = moderation_module.BanManager()
        ban_manager.ban_user(post_ip, duration_seconds=ban_for, boards=[ban_from], reason=ban_reason, moderator=session["username"])
        try:
            database_module.append_banned_warning_to_post(post_id, lang["banned-thread-warn"])
        except Exception:
            pass
        flash(lang["flash-user-banned"])
        current_app.extensions['socketio'].emit('ban_post', {
            'type': 'Ban Post',
            'post': {'id': post_id}
        }, broadcast=True)
    else:
        flash(lang["flash-user-ban-error"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/move_post/<post_id>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda post_id: database_module.get_post_board(post_id))
def move_post(post_id):
    new_board = request.form['new_board']
    lang = get_lang()
    if database_module.move_thread(int(post_id), new_board):
        flash(lang["flash-post-moved"].format(board=new_board))
        current_app.extensions['socketio'].emit('move_post', {
            'type': 'Move Post',
            'post': {'id': post_id, 'new_board': new_board}
        }, broadcast=True)
    else:
        flash(lang["flash-post-move-failed"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/add_board_staff/<board_uri>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda board_uri: board_uri)
def add_board_staff_route(board_uri):
    staff_username = request.form.get('username')
    lang = get_lang()
    if not staff_username:
        flash(lang["flash-no-username-provided"], 'danger')
        return redirect(request.referrer or '/')

    try:
        if database_module.add_board_staff(board_uri, staff_username):
            flash(lang["flash-staff-added"].format(username=staff_username, board=board_uri), 'success')
        else:
            flash(lang["flash-staff-add-failed"], 'danger')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        print(e)
        flash(lang["flash-unexpected-error"], 'danger')

    return redirect(request.referrer or '/')

@auth_bp.route('/api/remove_board_staff/<board_uri>', methods=['POST'])
@has_board_owner_or_admin_perms(lambda board_uri: board_uri)
def remove_board_staff_route(board_uri):
    staff_username = request.form.get('username')
    lang = get_lang()
    if not staff_username:
        flash(lang["flash-no-username-provided"], 'danger')
        return redirect(request.referrer or '/')

    try:
        if database_module.remove_board_staff(board_uri, staff_username):
            flash(lang["flash-staff-removed"].format(username=staff_username, board=board_uri), 'success')
        else:
            flash(lang["flash-staff-remove-failed"], 'danger')
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
    lang = get_lang()
    flash(lang["flash-timeout-removed"], 'success')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/remove_ban/<int:ban_id>', methods=['POST'])
def remove_ban(ban_id):
    if 'username' not in session:
        return redirect('/conta')

    username = session['username']
    roles = database_module.get_user_role(username)
    roles_lower = roles.lower() if roles else ''

    ban_manager = moderation_module.BanManager()

    if 'owner' in roles_lower or 'mod' in roles_lower:
        ban_manager.unban_user_by_id(ban_id)
        lang = get_lang()
        flash(lang["flash-ban-removed"], 'success')
        return redirect(request.referrer or '/')

    ban_records = ban_manager.db.query('bans', {'id': {'==': ban_id}})
    if not ban_records:
        lang = get_lang()
        flash(lang["flash-ban-not-found"], 'danger')
        return redirect(request.referrer or '/')

    ban = ban_records[0]
    boards = ban.get('boards') or []
    boards = [b for b in boards if b is not None]

    if not boards:
        flash('You do not have permission to remove this ban.', 'danger')
        return redirect(request.referrer or '/')

    all_boards = database_module.get_all_boards(include_stats=True)
    user_board_uris = set()
    for board in all_boards:
        board_uri = board.get('board_uri')
        if not board_uri:
            continue
        if board.get('board_owner') == username or username in board.get('board_staffs', []):
            user_board_uris.add(board_uri)

    if not user_board_uris or not set(boards).issubset(user_board_uris):
        lang = get_lang()
        flash(lang["flash-ban-remove-no-permission"], 'danger')
        return redirect(request.referrer or '/')

    ban_manager.unban_user_by_id(ban_id)
    lang = get_lang()
    flash(lang["flash-ban-removed"], 'success')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/auth_user', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if database_module.login_user(username, password):
        session['username'] = username
        session['role'] = database_module.get_user_role(username)
        return redirect('/conta')
    lang = get_lang()
    flash(lang["flash-invalid-credentials"], 'danger')
    return redirect('/conta')

@auth_bp.route('/api/register_user', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    captcha_text = request.form['captcha']
    if database_module.register_user(username, password, captcha_text, session['captcha_text']):
        return redirect('/conta')
    lang = get_lang()
    flash(lang["flash-something-went-wrong-retry"])
    session['form_data'] = request.form.to_dict()
    return redirect(request.referrer or '/')

@auth_bp.route('/api/create_board', methods=['POST'])
def create_board():
    # Check if board creation is allowed
    config_manager = moderation_module.ChanConfigManager()
    chan_config = config_manager.get_config()
    
    if not chan_config['free_board_creation']:
        username = session.get('username')
        lang = get_lang()
        if not username:
             flash(lang["flash-login-required-create-board"], 'danger')
             return redirect(request.referrer or '/')
             
        roles = database_module.get_user_role(username)
        if not roles or ('owner' not in roles.lower() and 'mod' not in roles.lower()):
            flash(lang["flash-board-creation-disabled"], 'danger')
            return redirect(request.referrer or '/')

    uri = request.form['uri']
    name = request.form['name']
    captcha_text = request.form['captcha']
    description = request.form['description']
    tags_input = request.form.get('tags', '')
    tag = tags_input.split('\n')[0].strip() if tags_input.strip() else 'Outros'
    
    if database_module.add_new_board(uri, name, description, session['username'], captcha_text, session['captcha_text'], tag):
        return redirect(f'/{uri}')
    lang = get_lang()
    flash(lang["flash-something-went-wrong-retry"])
    session['form_data'] = request.form.to_dict()
    return redirect(request.referrer or '/')

@auth_bp.route('/api/edit_board_info', methods=['POST'])
@has_board_owner_or_admin_perms(lambda: request.form.get('board_uri'))
def edit_board_info_route():
    board_uri = request.form['board_uri']
    new_owner = request.form['owner']
    new_name = request.form['name']
    new_desc = request.form['description']
    new_tag = request.form.get('tags', 'Outros').split('\n')[0].strip()
    require_media_approval = 1 if request.form.get('require_media_approval') == 'on' else 0
    allow_name = 1 if request.form.get('allow_name') == 'on' else 0

    default_poster_name = request.form.get('default_poster_name', '').strip()
    max_pages_raw = request.form.get('max_pages', '').strip()
    default_css = request.form.get('default_css') or ''

    max_pages_value = None
    if max_pages_raw != '':
        try:
            max_pages_value = int(max_pages_raw)
        except (TypeError, ValueError):
            max_pages_value = 0

    config_manager = moderation_module.ChanConfigManager()
    chan_config = config_manager.get_config()
    global_max_pages = int(chan_config.get('max_pages_per_board', 0) or 0)

    if global_max_pages > 0 and max_pages_value is not None and max_pages_value > global_max_pages:
        max_pages_value = global_max_pages
    
    if not database_module.check_user_exists(new_owner):
        lang = get_lang()
        flash(lang["flash-user-does-not-exist"].format(username=new_owner), 'danger')
        return redirect(request.referrer or '/')
    
    if database_module.edit_board_info(
        board_uri,
        new_owner,
        new_name,
        new_desc,
        new_tag,
        require_media_approval,
        default_poster_name=default_poster_name,
        max_pages=max_pages_value,
        default_css=default_css,
        allow_name=allow_name
    ):
        lang = get_lang()
        flash(lang["flash-global-defaults-updated"])
    else:
        lang = get_lang()
        flash(lang["flash-board-update-failed"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/upload_banner', methods=['POST'])
@has_board_owner_or_admin_perms(lambda: request.form.get('board_uri'))
def upload_banner():
    board_uri = request.form['board_uri']
    file = request.files.get('imageUpload')

    if not file or file.filename == '':
        lang = get_lang()
        flash(lang["flash-no-file-uploaded"], 'danger')
        return redirect(request.referrer or '/')
        
    # Sanitize board_uri to prevent LFI
    if not re.match(r'^[a-zA-Z0-9_]+$', board_uri):
        lang = get_lang()
        flash(lang["flash-invalid-board-uri"], 'danger')
        return redirect(request.referrer or '/')

    lang = get_lang()
    if allowed_file(file):
        directory = os.path.join(f'./static/imgs/banners/{board_uri}')
        os.makedirs(directory, exist_ok=True)
        
        # Generate random filename
        ext = os.path.splitext(file.filename)[1].lower()
        new_filename = f"{uuid.uuid4().hex}{ext}"
        
        file.save(os.path.join(directory, new_filename))
        flash(lang["flash-banner-uploaded"])
    else:
        flash(lang["flash-invalid-image-file"], 'danger')
    return redirect(request.referrer or '/')

@auth_bp.route('/api/delete_banner', methods=['POST'])
def delete_banner():
    if 'username' not in session:
        return redirect(url_for('boards.main_page'))
    
    username = session['username']
    board_uri = request.form.get('board_uri')
    banner_filename = request.form.get('banner_filename')
    
    if not board_uri or not banner_filename:
        lang = get_lang()
        flash(lang["flash-invalid-request"])
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
        lang = get_lang()
        if database_module.delete_board_banner(board_uri, banner_filename):
            flash(lang["flash-banner-deleted"])
        else:
            flash(lang["flash-banner-delete-error"])
    else:
        lang = get_lang()
        flash(lang["flash-banner-delete-no-permission"])
        
    return redirect(request.referrer)

@auth_bp.route('/api/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        lang = get_lang()
        flash(lang["flash-logged-out"], 'info')
    return redirect('/')

@auth_bp.route('/api/change_user_role', methods=['POST'])
@has_owner_perms
def change_user_role():
    target_username = request.form.get('username')
    new_role = request.form.get('role')
    
    if not target_username or new_role not in ['mod', 'user', 'owner']:
         lang = get_lang()
         flash(lang["flash-invalid-request-parameters"], 'danger')
         return redirect(request.referrer or '/conta/users')
         
    # Adjust role string for DB
    if new_role == 'user':
        new_role = ''
        
    if database_module.update_user_role(target_username, new_role):
        role_label = new_role if new_role else 'User'
        lang = get_lang()
        flash(lang["flash-user-role-updated"].format(username=target_username, role=role_label), 'success')
    else:
        lang = get_lang()
        flash(lang["flash-user-role-update-failed"], 'danger')
        
    return redirect(request.referrer or '/conta/users')
