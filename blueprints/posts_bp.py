from flask import current_app, Blueprint, render_template, redirect, request, flash, session
from database_modules import database_module, moderation_module, formatting
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from PIL import Image
import cv2
import re
import os

# Blueprint register
posts_bp = Blueprint('posts', __name__)
socketio = SocketIO()

class PostHandler:
    def __init__(self, socketio, user_ip, post_mode, post_name, board_id, comment, embed, captcha_input):
        self.socketio = socketio
        self.user_ip = user_ip
        self.post_mode = post_mode
        self.post_name = post_name
        self.board_id = board_id
        self.original_content = comment
        self.comment = formatting.format_comment(comment)
        self.embed = embed
        self.captcha_input = captcha_input
        
    timeout_manager = moderation_module.TimeoutManager()
    ban_manager = moderation_module.BanManager()
    
    def check_banned(self):
        banned_status = self.ban_manager.is_banned(self.user_ip)
        if banned_status.get('is_banned', True):
            flash(f"You has been banned, reason: {banned_status.get('reason')}")
            return False
        return True

    def check_timeout(self):
        timeout_status = self.timeout_manager.check_timeout(self.user_ip)
        if timeout_status.get('is_timeout', False):
            flash('Wait a few seconds to post again.')
            return False
        return True
    
    def validate_comment(self):
        if len(self.comment) >= 20000:
            flash('You reached the limit.')
            return False
        if self.comment == '':
            flash('You have to type something, you bastard.')
            return False
        return True
    
    def process_uploaded_files(self, upload_folder, is_thread=False):
        files = request.files.getlist('fileInput')
        saved_files = []
        thumb_paths = []
        
        # Determine thumbnail folder based on upload type
        thumb_folder = './static/post_images/thumbs/' if is_thread else './static/reply_images/thumbs/'
        os.makedirs(thumb_folder, exist_ok=True)
        
        for file in files:
            if file.filename != '' and file.filename.lower().endswith(('.jpeg', '.jpg', '.mov', '.gif', '.png', '.webp', '.webm', '.mp4')):
                # Generate unique filename
                filename = file.filename
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(upload_folder, filename)):
                    filename = f"{base}_{counter}{ext}"
                    counter += 1
                
                # Save file
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                saved_files.append(filename)
                
                # Generate thumbnail for videos
                if filename.lower().endswith(('.mp4', '.mov', '.webm')):
                    thumb_path = self.capture_frame_from_video(file_path, thumb_folder)
                    if thumb_path:
                        thumb_paths.append(thumb_path)
                    else:
                        print(f"Failed to generate thumbnail for {filename}")
        
        return saved_files, thumb_paths
    
    def handle_reply(self, reply_to):
        if not database_module.check_replyto_exist(int(reply_to)):
            flash("This thread don't even exist, dumb!")
            return False

        if database_module.verify_locked_thread(int(reply_to)):
            flash("This thread is locked.")
            return False
            
        if database_module.verify_board_captcha(self.board_id):
            if not database_module.validate_captcha(self.captcha_input, session["captcha_text"]):
                flash("Invalid captcha.")
                return False
        
        upload_folder = './static/reply_images/'
        os.makedirs(upload_folder, exist_ok=True)
        
        saved_files, _ = self.process_uploaded_files(upload_folder, is_thread=False)
        self.socketio.emit('nova_postagem', {
            'type': 'New Reply',
            'post': {
                'id': database_module.get_max_post_id() + 1,
                'thread_id': reply_to,
                'name': self.post_name,
                'content': self.comment,
                'files': saved_files,
                'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'board': self.board_id
            }
        }, broadcast=True)
        database_module.add_new_reply(self.user_ip, reply_to, self.post_name, self.comment, self.embed, saved_files)
        self.timeout_manager.apply_timeout(self.user_ip, duration_seconds=35, reason="Automatic timeout.")
        return True

    def capture_frame_from_video(self, video_path, thumb_folder=None):
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Error: Unable to open video.")

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_at_second = int(fps) if fps > 0 else 1

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_at_second)
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    raise ValueError("Error: Unable to read frame.")

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Use specified thumb folder or default to post thumbs
            if thumb_folder is None:
                thumb_folder = './static/post_images/thumbs/'
            
            os.makedirs(thumb_folder, exist_ok=True)

            base = os.path.splitext(os.path.basename(video_path))[0]
            thumbnail_filename = f"thumbnail_{base}.jpg"
            thumb_path = os.path.join(thumb_folder, thumbnail_filename)

            pil_image = Image.fromarray(image)
            pil_image.save(thumb_path)
            cap.release()

            return thumb_path
        except Exception as e:
            print(f"Error processing video: {e}")
            return None

    def handle_post(self):
        if database_module.verify_board_captcha(self.board_id):
            if not database_module.validate_captcha(self.captcha_input, session["captcha_text"]):
                flash("Invalid captcha.")
                return False
        
        upload_folder = './static/post_images/'
        os.makedirs(upload_folder, exist_ok=True)
        
        saved_files, thumb_paths = self.process_uploaded_files(upload_folder, is_thread=True)
        
        if not saved_files:
            flash("You need to upload at least one image/video to start a thread.")
            return False
        self.socketio.emit('nova_postagem', {
            'type': 'New Thread',
            'post': {
                'id': database_module.get_max_post_id() + 1,
                'name': self.post_name,
                'content': self.comment,
                'files': saved_files,
                'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'board': self.board_id,
                'role': 'user'  # or whatever role system you have
            }
        }, broadcast=True)
        database_module.add_new_post(self.user_ip, self.board_id, self.post_name, 
                                   self.original_content, self.comment, self.embed, saved_files)
        self.timeout_manager.apply_timeout(self.user_ip, duration_seconds=35, reason="Automatic timeout.")
        return True

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
    
    if formatting.filter_xss(comment) or formatting.filter_xss(post_name):
        flash('You cant use HTML tags.')
        return redirect(request.referrer)

    handler = PostHandler(socketio, user_ip, post_mode, post_name, board_id, comment, embed, captcha_input)

    if not handler.check_banned():
        return redirect(request.referrer)

    if not handler.check_timeout():
        return redirect(request.referrer)

    if post_mode == "reply":
        reply_to = request.form['thread_id']
        if not handler.validate_comment():
            return redirect(request.referrer)
        if not handler.handle_reply(reply_to):
            return redirect(request.referrer)
    else:
        match = re.match(r'^#(\d+)', comment)
        if match:
            reply_to = match.group(1)
            if not database_module.check_post_exist(int(reply_to)):
                reply_to = request.form.get('thread_id', '')
                if not reply_to:
                    flash("Invalid thread reference.")
                    return redirect(request.referrer)
            
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
