#imports
from flask import current_app, Blueprint, render_template, redirect, request, flash, session
from database_modules import database_module, timeout_module, formatting
from flask_socketio import SocketIO, emit
from PIL import Image
import cv2
import re
import os
#bluepint register.
posts_bp = Blueprint('posts', __name__)
#socketIO call.
socketio = SocketIO()
#post handling class.
class PostHandler:
    def __init__(self, socketio, user_ip, post_mode, post_name, board_id, comment, embed, captcha_input):
        self.socketio = socketio
        self.user_ip = user_ip
        self.post_mode = post_mode
        self.post_name = post_name
        self.board_id = board_id
        self.comment = formatting.format_comment(comment)
        self.embed = embed
        self.captcha_input = captcha_input
    #check if user is on hold or not.
    def check_timeout(self):
        if database_module.check_timeout_user(self.user_ip):
            flash('Wait a few seconds to post again.')
            return False
        return True
    #check if the post's board exists.
    def check_board(self):
        if not database_module.check_board(self.board_id):
            flash('I know what did you tried to do.')
            return False
        return True
    #post content handling.
    def validate_comment(self):
        if len(self.comment) >= 10000:
            flash('You reached the limit.')
            return False
        if self.comment == '':
            flash('You have to type somethig, you bastard.')
            return False
        
        return True
    #reply post handling.
    def handle_reply(self, reply_to):
        if database_module.verify_locked_thread(int(reply_to)):
            flash("This thread is locked.")
            return False
        if database_module.verify_board_captcha(self.board_id):
            if not database_module.validate_captcha(self.captcha_input, session["captcha_text"]):
                flash("Invalid captcha.")
                return False
        if 'fileInput' in request.files:
            file = request.files['fileInput']
            if file.filename!= '' and file.filename.endswith(('.jpeg','.mov', '.jpg', '.gif', '.png', '.webp', '.webm', '.mp4')):
                upload_folder = './static/reply_images/'
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, file.filename))
                database_module.add_new_reply(self.user_ip, reply_to, self.post_name, self.comment, self.embed, file.filename)
                self.socketio.emit('nova_postagem', 'New Reply', broadcast=True)
                timeout_module.timeout(self.user_ip)
                return True
        file = ""
        database_module.add_new_reply(self.user_ip, reply_to, self.post_name, self.comment, self.embed, file)
        self.socketio.emit('nova_postagem', 'New Reply', broadcast=True)
        timeout_module.timeout(self.user_ip)
        return True
    #generate videos thumbnail
    def capture_frame_from_video(self, video_path):
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Error: Unable to open video.")

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_at_second = int(fps)  

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_at_second)

            ret, frame = cap.read()
            if not ret:
                raise ValueError("Error: Unable to read frame.")

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            thumb_folder = './static/post_images/thumbs/'
            os.makedirs(thumb_folder, exist_ok=True)

            base, ext = os.path.splitext(os.path.basename(video_path))
            thumbnail_filename = f"thumbnail_{base}.jpg"
            thumb_path = os.path.join(thumb_folder, thumbnail_filename)

            pil_image = Image.fromarray(image)
            pil_image.save(thumb_path)

            cap.release()

            return thumb_path

        except Exception as e:
            print(f"Error processing video: {e}")
            return None

    #thread post handling.
    def handle_post(self):
        if database_module.verify_board_captcha(self.board_id):
            if not database_module.validate_captcha(self.captcha_input, session["captcha_text"]):
                flash("Invalid captcha.")
                return False
        if 'fileInput' in request.files and self.post_mode != 'reply':
            file = request.files['fileInput']
            if file.filename!= '' and file.filename.endswith(('.jpeg', '.jpg','.mov', '.gif', '.png', '.webp', '.webm', '.mp4')):
                upload_folder = './static/post_images/'
                os.makedirs(upload_folder, exist_ok=True)
                filename = file.filename
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(upload_folder, filename)):
                    filename = f"{base}_{counter}{ext}"
                    counter += 1
                file.save(os.path.join(upload_folder, filename))
                
                if filename.endswith(('.mp4', '.mov', '.webm')):
                    thumb_path = self.capture_frame_from_video(os.path.join(upload_folder, filename))
                    if thumb_path:
                        print(f"Thumbnail saved at: {thumb_path}")
                    else:
                        flash("Error generating thumbnail from video.")
                        return False

                database_module.add_new_post(self.user_ip, self.board_id, self.post_name, self.comment, self.embed, filename)
                self.socketio.emit('nova_postagem', 'New Reply', broadcast=True)
                timeout_module.timeout(self.user_ip)
                return True
        
        if self.post_mode != 'reply':
            flash("You have to upload some image, this is an imageboard...")
            return False
#new post endpoint.
@posts_bp.route('/new_post', methods=['POST'])
def new_post():
    socketio = current_app.extensions['socketio']
    user_ip = request.remote_addr
    post_mode = request.form["post_mode"]
    post_name = request.form["name"]
    board_id = request.form['board_id']
    comment = request.form['text']
    embed = request.form['embed']
    captcha_input = 'none'
    if database_module.verify_board_captcha(board_id):
        captcha_input = request.form['captcha']
    
    if formatting.filter_xss(comment):
        flash('You cant use html tags.')
        return redirect(request.referrer)
    
    if formatting.filter_xss(post_name):
        flash('You cant use html tags.')
        return redirect(request.referrer)

    handler = PostHandler(socketio, user_ip, post_mode, post_name, board_id, comment, embed, captcha_input)

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
