from flask import current_app, Blueprint, render_template, redirect, request
from database_modules import database_module

boards_bp = Blueprint('boards', __name__)

@boards_bp.route('/')
def main_page():
    posts = database_module.load_db()
    boards = database_module.load_boards()
    return render_template('index.html',boards=boards,all_posts=reversed(posts),posts=reversed(posts[-6:]))

@boards_bp.route('/tabuas')
def tabuas():
    boards = database_module.load_boards()
    posts = database_module.load_db()
    return render_template('tabuas.html',all_posts=reversed(posts),boards=boards)

@boards_bp.route('/<board_name>/')
def board_b(board_name):
    if not database_module.check_board(board_name):
        return redirect(request.referrer)
    posts = database_module.load_db()
<<<<<<< HEAD
    replies = database_module.load_replies()
    return render_template('board.html', posts=reversed(posts),replies=replies,board_id=board_name)
=======
    post_mode = "normal_thread"
    replies = database_module.load_replies()
    return render_template('board.html', posts=reversed(posts),replies=replies,board_id=board_name, post_mode=post_mode)
>>>>>>> 147da1f (Atualizações significantes)

@boards_bp.route('/<board_name>/thread/<thread_id>')
def replies(board_name, thread_id):
    board_id = board_name
    posts = database_module.load_db()
<<<<<<< HEAD
=======
    post_mode = "reply"
>>>>>>> 147da1f (Atualizações significantes)
    replies = database_module.load_replies()
    thread_found = False
    board_posts = []
    post_replies = []
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
<<<<<<< HEAD
    return render_template('thread_reply.html', posts=board_posts, replies=post_replies,board_id=board_id,thread_id=int(thread_id))
=======
    return render_template('thread_reply.html', posts=board_posts, replies=post_replies,board_id=board_id,thread_id=int(thread_id), post_mode=post_mode)
>>>>>>> 147da1f (Atualizações significantes)
