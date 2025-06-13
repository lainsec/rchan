#imports
from flask import current_app, Blueprint, render_template, session, redirect, request, url_for
from database_modules import database_module, language_module
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
        user_boards = user_boards=database_module.get_user_boards(session["username"])
        all_boards = database_module.get_all_boards(include_stats=True)
        roles = database_module.get_user_role(session["username"])
        return render_template('dashboard.html',database_module=database_module, username=session["username"],roles=roles,user_boards=user_boards, all_boards=all_boards)
    return render_template('login.html')
#register page route.
@boards_bp.route('/registrar')
def register():
    if 'username' in session:
        return redirect('/conta')
    captcha_text, captcha_image = database_module.generate_captcha()
    session['captcha_text'] = captcha_text
    print(session['captcha_text'])
    return render_template('register.html',captcha_image=captcha_image)
#board creation page route.
@boards_bp.route('/create')
def create():
    if 'username' in session:
        captcha_text, captcha_image = database_module.generate_captcha()
        session['captcha_text'] = captcha_text
        return render_template('board-create.html',captcha_image=captcha_image)
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
        board_id=board_uri,)
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
    
    return render_template(
        'catalog.html',
        board_info=board_info,
        captcha_image=captcha_image,
        roles=roles,
        pinneds=pinneds,
        posts=posts,
        replies=replies,
        board_banner=board_banner,
        board_id=board_uri,)
#board banners page route.
@boards_bp.route('/<board_uri>/banners')
def board_banners(board_uri):
    if "username" in session:
        username = session['username']
    else:
        username = 'anon'
    board_info = database_module.get_board_info(board_uri)
    board_banner = database_module.get_board_banner(board_uri)
    banners = database_module.get_all_banners(board_uri)
    return render_template('board_banners.html',username=username,board_banner=board_banner,banners=banners,board_id=board_uri,board_info=board_info)
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

    return render_template(
        'thread_reply.html',
        captcha_image=captcha_image,
        board_info=board_info,
        posts=thread,  # The original post
        replies=post_replies,
        board_id=board_name,
        thread_id=thread_id,
        post_mode="reply",
        roles=roles
    )
