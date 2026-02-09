#imports
from flask import current_app, Blueprint, render_template, session, redirect, request, url_for, flash
from database_modules import database_module, language_module
from database_modules.moderation_module import TimeoutManager, BanManager
#blueprint register.
boards_bp = Blueprint('boards', __name__)
#load language.
@boards_bp.context_processor
def inject_lang():
    lang = language_module.get_user_lang('default')
    return dict(lang=lang)
#load nav boards
@boards_bp.context_processor
def globalboards():
    boards = database_module.get_all_boards(include_stats=True)
    return {"boards": boards}
#load custom themes
@boards_bp.context_processor
def customthemes():
    custom_themes_list = database_module.get_custom_themes()
    return {"custom_themes": custom_themes_list}
#error handling.
@boards_bp.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('boards.main_page'))
#landing page route.
@boards_bp.route('/')
def main_page():
    posts = database_module.get_all_posts()
    return render_template('index.html',all_posts=posts,posts=reversed(posts[-6:]))
#boards page route.
@boards_bp.route('/tabuas')
def tabuas():
    posts = database_module.get_all_posts()
    return render_template('tabuas.html',all_posts=posts)
#account dashboard and login route.
@boards_bp.route('/conta')
def login():
    if 'username' in session:
        username = session["username"]
        user_boards = database_module.get_user_boards(username)
        all_boards = database_module.get_all_boards(include_stats=True)
        roles = database_module.get_user_role(username)
        
        # Extended data for dashboard
        popular_boards = database_module.get_popular_boards(limit=5)
        recent_posts = database_module.get_all_posts(sort_by_date=True)[:10]
        
        # Moderation data
        timeout_manager = TimeoutManager()
        ban_manager = BanManager()
        active_timeouts = timeout_manager.get_active_timeouts()
        active_bans = ban_manager.get_active_bans()
        
        return render_template('dashboard.html',
                             database_module=database_module, 
                             username=username,
                             roles=roles,
                             user_boards=user_boards, 
                             all_boards=all_boards,
                             popular_boards=popular_boards,
                             recent_posts=recent_posts,
                             active_timeouts=active_timeouts,
                             active_bans=active_bans)
    return render_template('login.html')

@boards_bp.route('/conta/users')
def users_dashboard():
    if 'username' not in session:
        return redirect('/conta')
        
    username = session["username"]
    roles = database_module.get_user_role(username)
    
    # Check permissions (Owner or Mod)
    if not roles or ('owner' not in roles.lower() and 'mod' not in roles.lower()):
        return redirect('/conta')
        
    # Handle pagination
    try:
        page = int(request.args.get('page', '1'))
    except ValueError:
        page = 1
    
    search_query = request.args.get('search', '')
    
    users_per_page = 20
    offset = (page - 1) * users_per_page
    
    users = database_module.get_all_registered_users(offset=offset, limit=users_per_page, search_query=search_query)
    total_users = database_module.count_all_registered_users(search_query=search_query)
    total_pages = (total_users + users_per_page - 1) // users_per_page
    
    return render_template('users_dashboard.html',
                         username=username,
                         roles=roles,
                         users=users,
                         page=page,
                         total_pages=total_pages,
                         search_query=search_query,
                         database_module=database_module)

#register page route.
@boards_bp.route('/registrar')
def register():
    if 'username' in session:
        return redirect('/conta')
    captcha_text, captcha_image = database_module.generate_captcha()
    session['captcha_text'] = captcha_text
    print(session['captcha_text'])
    form_data = session.pop('form_data', {})
    return render_template('register.html',captcha_image=captcha_image, form_data=form_data)

@boards_bp.route('/create')
def create():
    if 'username' in session:
        captcha_text, captcha_image = database_module.generate_captcha()
        session['captcha_text'] = captcha_text
        form_data = session.pop('form_data', {})
        return render_template('board-create.html',captcha_image=captcha_image, form_data=form_data)
    else:
        return redirect('/conta')   
#rules route page
@boards_bp.route('/pages/globalrules.html')
def global_rules():
    return render_template('pages/globalrules.html')
#board page endpoint
@boards_bp.route('/<board_uri>/')
def board_page(board_uri):
    # Check if board exists
    if not database_module.get_board_info(board_uri):
        return redirect(url_for('boards.main_page'))
    
    # Handle pagination
    try:
        page = int(request.args.get('page', '1'))
    except ValueError:
        page = 1
    
    posts_per_page = 6
    offset = (page - 1) * posts_per_page
    
    # Get board content
    posts = database_module.load_db_page(board_uri, offset=offset, limit=posts_per_page)
    pinneds = database_module.get_pinned_posts(board_uri)
    board_info = database_module.get_board_info(board_uri)
    board_banner = database_module.get_board_banner(board_uri)

    total_posts = database_module.count_posts_in_board(board_uri)
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    # Generate CAPTCHA
    captcha_text, captcha_image = database_module.generate_captcha()
    session['captcha_text'] = captcha_text
    
    # Get replies for the current page's posts (alternative method)
    visible_post_ids = [post['post_id'] for post in posts]
    all_replies = database_module.DB.find_all('replies')
    replies = [reply for reply in all_replies if reply['post_id'] in visible_post_ids]
    
    # Get user role if logged in
    roles = 'none'
    if 'username' in session:
        roles = database_module.get_user_role(session["username"])
    
    form_data = session.pop('form_data', {})

    return render_template(
        'board.html',
        board_info=board_info,
        captcha_image=captcha_image,
        roles=roles,
        page=page,
        posts_per_page=posts_per_page,
        total_pages=total_pages,
        pinneds=pinneds,
        posts=posts,
        replies=replies,
        board_banner=board_banner,
        board_id=board_uri,
        form_data=form_data)
#board catalog page endpoint
@boards_bp.route('/<board_uri>/catalog')
def board_catalog(board_uri):
    # Check if board exists
    if not database_module.get_board_info(board_uri):
        return redirect(url_for('boards.main_page'))

    posts = database_module.load_db_page(board_uri, limit=75)
    pinneds = database_module.get_pinned_posts(board_uri)
    board_info = database_module.get_board_info(board_uri)
    board_banner = database_module.get_board_banner(board_uri)
    
    # Generate CAPTCHA
    captcha_text, captcha_image = database_module.generate_captcha()
    session['captcha_text'] = captcha_text
    
    # Get replies for the current page's posts (alternative method)
    visible_post_ids = [post['post_id'] for post in posts]
    all_replies = database_module.DB.find_all('replies')
    replies = [reply for reply in all_replies if reply['post_id'] in visible_post_ids]
    
    # Get user role if logged in
    roles = 'none'
    if 'username' in session:
        roles = database_module.get_user_role(session["username"])
    
    form_data = session.pop('form_data', {})

    return render_template(
        'catalog.html',
        board_info=board_info,
        captcha_image=captcha_image,
        roles=roles,
        pinneds=pinneds,
        posts=posts,
        replies=replies,
        board_banner=board_banner,
        board_id=board_uri,
        form_data=form_data)
#board banners page route.
@boards_bp.route('/<board_uri>/banners')
def board_banners(board_uri):
    roles = 'none'
    if "username" in session:
        username = session['username']
        roles = database_module.get_user_role(session["username"])
    else:
        username = 'anon'
    board_info = database_module.get_board_info(board_uri)
    board_banner = database_module.get_board_banner(board_uri)
    banners = database_module.get_all_banners(board_uri)
    return render_template('board_banners.html',username=username,board_banner=board_banner,banners=banners,board_id=board_uri,board_info=board_info, roles=roles)

#thread page route.
@boards_bp.route('/<board_name>/thread/<thread_id>')
def replies(board_name, thread_id):
    # Verify board exists
    board_info = database_module.get_board_info(board_name)
    if not board_info:
        return redirect(url_for('boards.main_page'))

    # Validate thread_id
    try:
        thread_id = int(thread_id)
    except ValueError:
        return redirect(request.referrer or url_for('boards.main_page'))

    # Check if thread exists
    thread = database_module.DB.query('posts', {
        'post_id': {'==': thread_id}, 
        'board': {'==': board_name}
    })
    if not thread:
        return redirect(url_for('boards.main_page'))

    # Get all replies for this thread (alternative method since 'in' operator isn't supported)
    all_replies = database_module.DB.find_all('replies')
    post_replies = [reply for reply in all_replies if reply.get('post_id') == thread_id]

    # Generate CAPTCHA
    captcha_text, captcha_image = database_module.generate_captcha()
    session['captcha_text'] = captcha_text

    # Get user role if logged in
    roles = 'none'
    if 'username' in session:
        roles = database_module.get_user_role(session["username"])

    form_data = session.pop('form_data', {})

    return render_template(
        'thread_reply.html',
        captcha_image=captcha_image,
        board_info=board_info,
        posts=thread,  # The original post
        replies=post_replies,
        board_id=board_name,
        thread_id=thread_id,
        post_mode="reply",
        roles=roles,
        form_data=form_data
    )