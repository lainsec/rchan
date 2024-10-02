from flask import current_app, Blueprint, render_template, redirect, request, flash, session
from database_modules import database_module, timeout_module
from flask_socketio import SocketIO, emit
import re
import os

posts_bp = Blueprint('posts', __name__)
socketio = SocketIO()

class PostHandler:
    def __init__(self, socketio, user_ip, post_mode, post_name, board_id, comment, embed):
        self.socketio = socketio
        self.user_ip = user_ip
        self.post_mode = post_mode
        self.post_name = post_name
        self.board_id = board_id
        self.comment = comment
        self.embed = embed

    def check_timeout(self):
        if database_module.check_timeout_user(self.user_ip):
            flash('você precisa esperar um pouco para postar novamente.')
            return False
        timeout_module.timeout(self.user_ip)
        return True

    def check_board(self):
        if not database_module.check_board(self.board_id):
            flash('Eu sei oq vc tentou fazer, seu bobão.')
            return False
        return True

    def validate_comment(self):
        if len(self.comment) >= 10000:
            flash('Você atingiu o limite')
            return False
        if self.comment == '':
            flash('Você precisa digitar algo, seu bocó!')
            return False
        return True

    def handle_reply(self, reply_to):
        if 'fileInput' in request.files:
            file = request.files['fileInput']
            if file.filename!= '' and file.filename.endswith(('.jpeg','.mov', '.jpg', '.gif', '.png', '.webp', '.webm', '.mp4')):
                upload_folder = './static/reply_images/'
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, file.filename))
                database_module.add_new_reply(self.user_ip, reply_to, self.post_name, self.comment, self.embed, file.filename)
                self.socketio.emit('nova_postagem', 'New Reply', broadcast=True)
                return True
        file = ""
        database_module.add_new_reply(self.user_ip, reply_to, self.post_name, self.comment, self.embed, file)
        self.socketio.emit('nova_postagem', 'New Reply', broadcast=True)
        return True

    def handle_post(self):
        if 'fileInput' in request.files and self.post_mode != 'reply':
            file = request.files['fileInput']
            if file.filename!= '' and file.filename.endswith(('.jpeg', '.jpg','.mov', '.gif', '.png', '.webp', '.webm', '.mp4')):
                upload_folder = './static/post_images/'
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, file.filename))
                database_module.add_new_post(self.user_ip, self.board_id, self.post_name, self.comment, self.embed, file.filename)
                self.socketio.emit('nova_postagem', 'New Reply', broadcast=True)
                return True
        
        if self.post_mode != 'reply':
            flash("Você precisa upar alguma imagem, isso é um imageboard...")
            return False

@posts_bp.route('/new_post', methods=['POST'])
def new_post():
    socketio = current_app.extensions['socketio']
    user_ip = session["user_ip"]
    post_mode = request.form["post_mode"]
    post_name = request.form["name"]
    board_id = request.form['board_id']
    comment = request.form['text']
    embed = request.form['embed']

    handler = PostHandler(socketio, user_ip, post_mode, post_name, board_id, comment, embed)

    if not handler.check_timeout():
        return redirect(request.referrer)
    if not handler.check_board():
        return redirect(request.referrer)

    if post_mode == "reply":
        reply_to = request.form['thread_id']
        if not handler.validate_comment():
            return redirect(request.referrer)
        if not handler.handle_reply(reply_to):
            return redirect(request.referrer)

    match = re.match(r'^#(\d+)', comment)
    if match:
        if post_mode == "reply":
            return redirect(request.referrer)
        reply_to = match.group(1)
        if not database_module.check_post_exist(int(reply_to)):
            reply_to = request.form['thread_id']
            if reply_to == '':
                reply_to = match.group(1)
        if not handler.handle_reply(reply_to):
            return redirect(request.referrer)
    else:
        if not handler.validate_comment():
            return redirect(request.referrer)
        if not handler.handle_post():
            return redirect(request.referrer)
    return redirect(request.referrer)

@posts_bp.route('/socket.io/')
def socket_io():
    socketio_manage(request.environ, {'/': SocketIOHandler}, request=request)
