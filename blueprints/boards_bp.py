from flask import current_app, Blueprint, render_template, session, redirect, request
from database_modules import database_module
from database_modules import language_module

boards_bp = Blueprint('boards', __name__)

@boards_bp.context_processor
def inject_lang():
    lang = language_module.get_user_lang('default')
    return dict(lang=lang)

@boards_bp.route('/')
def main_page():
    posts = database_module.load_db()
    boards = database_module.load_boards()
    return render_template('index.html',boards=boards,all_posts=posts,posts=reversed(posts[-6:]))

@boards_bp.route('/tabuas')
def tabuas():
    boards = database_module.load_boards()
    posts = database_module.load_db()
    return render_template('tabuas.html',all_posts=posts,boards=boards)

@boards_bp.route('/conta')
def login():
    if 'username' in session:
        user_boards = user_boards=database_module.get_user_boards(session["username"])
        all_boards = database_module.load_boards()
        roles = database_module.get_user_role(session["username"])
        return render_template('dashboard.html', username=session["username"],roles=roles,user_boards=user_boards, all_boards=all_boards)
    return render_template('login.html')

@boards_bp.route('/registrar')
def register():
    if 'username' in session:
        return redirect('/conta')
    captcha_text, captcha_image = database_module.generate_captcha()
    session['captcha_text'] = captcha_text
    print(session['captcha_text'])
    return render_template('register.html',captcha_image=captcha_image)

@boards_bp.route('/create')
def create():
    if 'username' in session:
        captcha_text, captcha_image = database_module.generate_captcha()
        session['captcha_text'] = captcha_text
        return render_template('board-create.html',captcha_image=captcha_image)
    else:
        return redirect('/conta')

@boards_bp.route('/<board_uri>/')
def board_page(board_uri):
    if not database_module.check_board(board_uri):
        return redirect(request.referrer)
    page_arg = request.args.get('page', '1') 
    try:
        page = int(page_arg)
    except ValueError:
        page = 1
    posts_per_page = 6
    posts = database_module.load_db_page(board_uri, offset=(page - 1) * posts_per_page, limit=posts_per_page)
    pinneds = database_module.get_pinned_posts(board_uri)
    board_info = database_module.get_board_info(board_uri)
    board_banner = database_module.get_board_banner(board_uri)
    post_mode = "normal_thread"
    captcha_text, captcha_image = database_module.generate_captcha()
    session['captcha_text'] = captcha_text
    replies = database_module.load_replies()
    return render_template('board.html',captcha_image=captcha_image, page=page, posts_per_page=posts_per_page, pinneds=pinneds, posts=posts,replies=replies,board_banner=board_banner,board_id=board_uri,board_info=board_info, post_mode=post_mode)

@boards_bp.route('/<board_uri>/banners')
def board_banners(board_uri):
    if not database_module.check_board(board_uri):
        return redirect(request.referrer)
    if "username" in session:
        username = session['username']
    else:
        username = 'anon'
    board_info = database_module.get_board_info(board_uri)
    board_banner = database_module.get_board_banner(board_uri)
    banners = database_module.get_all_banners(board_uri)
    return render_template('board_banners.html',username=username,board_banner=board_banner,banners=banners,board_id=board_uri,board_info=board_info)

@boards_bp.route('/<board_uri>/manage')
def board_mod(board_uri):
    if 'username' in session:
        board_info = database_module.get_board_info(board_uri)
        if 'mod'.lower() in session["role"].lower() or 'owner'.lower() in session["role"].lower() or session["username"] == board_info.get('board_owner'):
            if not database_module.check_board(board_uri):
                return redirect(request.referrer)
            posts = database_module.load_db()
            board_banner = database_module.get_board_banner(board_uri)
            post_mode = "normal_thread"
            replies = database_module.load_replies()
            return render_template('mod_board.html', board_banner=board_banner,posts=reversed(posts),replies=replies,board_id=board_uri,board_info=board_info, post_mode=post_mode)
        else:
            return redirect(request.referrer)
    return redirect(request.referrer)

@boards_bp.route('/<board_name>/thread/<thread_id>')
def replies(board_name, thread_id):
    board_id = board_name
    board_info = database_module.get_board_info(board_id)
    posts = database_module.load_db()
    post_mode = "reply"
    replies = database_module.load_replies()
    thread_found = False
    board_posts = []
    post_replies = []
    captcha_text, captcha_image = database_module.generate_captcha()
    session['captcha_text'] = captcha_text
    for post in posts:
        if post['post_id'] == int(thread_id):
            thread_found = True
    if not thread_found:
        return redirect('/')
    for post in posts:
        if post.get('post_id') == int(thread_id):
            board_posts.append(post)
    for reply in replies:
        if reply.get('post_id') == int(thread_id):
            post_replies.append(reply)
    return render_template('thread_reply.html',captcha_image=captcha_image, board_info=board_info, posts=board_posts, replies=post_replies,board_id=board_id,thread_id=int(thread_id), post_mode=post_mode)
