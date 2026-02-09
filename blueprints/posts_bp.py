from flask import current_app, Blueprint, render_template, redirect, request, flash, session
from database_modules import database_module, moderation_module, formatting
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from PIL import Image, ImageOps
import magic
import cv2
import re
import os

# Blueprint register
posts_bp = Blueprint('posts', __name__)
socketio = SocketIO()
# Post handling class
class PostHandler:
    def __init__(self, socketio, user_ip, post_mode, post_name, post_subject, board_id, comment, embed, captcha_input):
        self.socketio = socketio
        self.user_ip = user_ip
        self.account_name = '' if not 'username' in session else session['username']
        self.post_mode = post_mode
        self.post_name = formatting.escape_html_post_info(post_name)
        self.post_subject = formatting.escape_html_post_info(post_subject)
        self.board_id = board_id
        self.original_content = comment
        self.comment = formatting.format_comment(comment)
        self.embed = embed
        self.captcha_input = captcha_input
    # Init the managers    
    timeout_manager = moderation_module.TimeoutManager()
    ban_manager = moderation_module.BanManager()
    # Check if the user is banned
    def check_banned(self):
        banned_status = self.ban_manager.is_banned(self.user_ip)
        print(banned_status)
        if not banned_status.get('is_banned', False):
            return True
        boards = banned_status.get('boards')
        if boards is None or boards == [] or None in boards:
            flash(f"You are banned from this board, reason: {banned_status.get('reason')}")
            return False
        if self.board_id in boards:
            flash(f"You are banned from this board, reason: {banned_status.get('reason')}")
            return False
        return True
    # Check if the user is in timeout
    def check_timeout(self):
        timeout_status = self.timeout_manager.check_timeout(self.user_ip)
        if timeout_status.get('is_timeout', False):
            flash('Wait a few seconds to post again.')
            return False
        return True
    # Validate the comment length and content
    def validate_comment(self):
        if len(self.comment) >= 20000:
            flash('You reached the limit.')
            return False
        if self.comment == '':
            flash('You have to type something, you bastard.')
            return False
        return True
    # Process uploaded files
    def process_uploaded_files(self, upload_folder, is_thread=False):
        files = request.files.getlist('fileInput')
        saved_files = []
        thumb_paths = []

        # Allowed MIME types
        allowed_mime_types = {
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'video/mp4',
            'video/quicktime',
            'video/webm'
        }

        # Thumbs folder
        thumb_folder = './static/post_images/thumbs/' if is_thread else './static/reply_images/thumbs/'
        os.makedirs(thumb_folder, exist_ok=True)

        for file in files:
            if file.filename != '' and file.filename.lower().endswith(('.jpeg', '.jpg', '.mov', '.gif', '.png', '.webp', '.webm', '.mp4')):
                # Verify the real type of the content
                file_head = file.stream.read(2048)  # Read the first bytes
                mime_type = magic.from_buffer(file_head, mime=True)
                file.stream.seek(0)  # Go to the start to save

                if mime_type not in allowed_mime_types:
                    flash("Stop trying to hack the website, bruh.")
                    return [], []

                # Generate new file name
                filename = os.path.basename(file.filename)
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(upload_folder, filename)):
                    filename = f"{base}_{counter}{ext}"
                    counter += 1

                # save the file with metadata stripping for images
                file_path = os.path.join(upload_folder, filename)
                
                if mime_type.startswith('image/'):
                    try:
                        img = Image.open(file.stream)
                        
                        # Check for animated GIF BEFORE any processing
                        if img.format == 'GIF' and getattr(img, "is_animated", False):
                            # Fallback to saving original stream for animated GIFs to preserve animation
                            file.stream.seek(0)
                            file.save(file_path)
                            saved_files.append(filename)
                            continue

                        # Apply EXIF rotation correction
                        img = ImageOps.exif_transpose(img)
                        
                        # Strip metadata by creating a new image or saving without exif
                        # ImageOps.exif_transpose returns a copy with rotation applied and orientation tag removed
                        # We just need to clear the info dictionary to be sure
                        img.info = {}
                        
                        # Handle formats
                        format = img.format
                        if not format:
                            ext_lower = os.path.splitext(filename)[1].lower()
                            if ext_lower in ['.jpg', '.jpeg']:
                                format = 'JPEG'
                            elif ext_lower == '.png':
                                format = 'PNG'
                            elif ext_lower == '.webp':
                                format = 'WEBP'
                            elif ext_lower == '.gif':
                                format = 'GIF'
                        
                        # Convert RGBA to RGB for JPEG
                        if format == 'JPEG' and img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                            
                        img.save(file_path, format=format, quality=95, optimize=True)
                            
                    except Exception as e:
                        print(f"Error stripping metadata for {filename}: {e}")
                        # Fallback to original save
                        file.stream.seek(0)
                        file.save(file_path)
                else:
                    # Videos and others
                    file.save(file_path)
                    
                saved_files.append(filename)

                # Generate the thumbnail, if its a video.
                if filename.lower().endswith(('.mp4', '.mov', '.webm')):
                    thumb_path = self.capture_frame_from_video(file_path, thumb_folder)
                    if thumb_path:
                        thumb_paths.append(thumb_path)
                    else:
                        print(f"Error generating thumb for: {filename}")

        return saved_files, thumb_paths
    # Process embed links (YouTube)
    def process_embed(self):
        if not self.embed:
            return None
        
        # Regex for YouTube
        youtube_regex = r'(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|embed/)|youtu\.be/)([\w-]+)'
        match = re.search(youtube_regex, self.embed)
        if match:
            return f"youtube:{match.group(1)}"
        return None

    # Handle reply posts
    def handle_reply(self, reply_to):
        if not database_module.check_replyto_exist(int(reply_to)):
            flash("This thread don't even exist, dumb!")
            return False
        # Check if the thread is locked
        if database_module.verify_locked_thread(int(reply_to)):
            flash("This thread is locked.")
            return False
        # check if the captcha is correct
        if database_module.verify_board_captcha(self.board_id):
            if not database_module.validate_captcha(self.captcha_input, session["captcha_text"]):
                flash("Invalid captcha.")
                return False
        
        upload_folder = './static/reply_images/'
        os.makedirs(upload_folder, exist_ok=True)
        
        saved_files, _ = self.process_uploaded_files(upload_folder, is_thread=False)
        
        # Process embed
        embed_file = self.process_embed()
        if embed_file:
            saved_files.append(embed_file)

        name_parts = self.post_name.split('#', 1)
        display_name = name_parts[0]
        tripcode_html = ''
        if len(name_parts) > 1:
            tripcode_html = f' <span class="tripcode">[tripcode protected]</span>'
        self.socketio.emit('nova_postagem', {
            'type': 'New Reply',
            'post': {
                'id': database_module.get_max_post_id() + 1,
                'thread_id': reply_to,
                'name': f'{display_name}{tripcode_html}',
                'subject': self.post_subject,
                'content': self.comment,
                'files': saved_files,
                'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'board': self.board_id
            }
        }, broadcast=True)
        database_module.add_new_reply(self.user_ip, self.account_name, self.post_subject, reply_to, self.post_name, self.comment, self.embed, saved_files)
        self.timeout_manager.apply_timeout(self.user_ip, duration_seconds=35, reason="Automatic timeout.")
        return True
    # Capture a frame from the video to use as thumbnail
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
    # Handle new thread posts
    def handle_post(self):
        if database_module.verify_board_captcha(self.board_id):
            if not database_module.validate_captcha(self.captcha_input, session["captcha_text"]):
                flash("Invalid captcha.")
                return False
        
        upload_folder = './static/post_images/'
        os.makedirs(upload_folder, exist_ok=True)
        
        saved_files, thumb_paths = self.process_uploaded_files(upload_folder, is_thread=True)
        
        # Process embed
        embed_file = self.process_embed()
        if embed_file:
            saved_files.append(embed_file)
        
        if not saved_files:
            flash("You need to upload at least one image/video to start a thread.")
            return False
        name_parts = self.post_name.split('#', 1)
        display_name = name_parts[0]
        tripcode_html = ''
        if len(name_parts) > 1:
            tripcode_html = f' <span class="tripcode">[tripcode protected]</span>'
        self.socketio.emit('nova_postagem', {
            'type': 'New Thread',
            'post': {
                'id': database_module.get_max_post_id() + 1,
                'name': f'{display_name}{tripcode_html}',
                'subject': self.post_subject,
                'content': self.comment,
                'files': saved_files,
                'date': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'board': self.board_id,
                'role': 'user'
            }
        }, broadcast=True)
        database_module.add_new_post(self.user_ip, self.account_name, self.board_id, self.post_subject, self.post_name, 
                                   self.original_content, self.comment, self.embed, saved_files)
        self.timeout_manager.apply_timeout(self.user_ip, duration_seconds=35, reason="Automatic timeout.")
        return True
# Route to handle new posts
@posts_bp.route('/api/new_post', methods=['POST'])
def new_post():
    socketio = current_app.extensions['socketio']
    user_ip = request.remote_addr
    post_mode = request.form["post_mode"]
    post_name = request.form["name"]
    post_subject = request.form["subject"]
    board_id = request.form['board_id']
    comment = request.form['text']
    embed = request.form['embed']
    captcha_input = 'none'
    
    if database_module.verify_board_captcha(board_id):
        captcha_input = request.form['captcha']
    
    if formatting.filter_xss(comment) or formatting.filter_xss(post_name):
        flash('You cant use HTML tags.')
        session['form_data'] = request.form.to_dict()
        return redirect(request.referrer)

    handler = PostHandler(socketio, user_ip, post_mode, post_name, post_subject, board_id, comment, embed, captcha_input)
    
    if len(post_name) > 40:
        flash("You've reached the limit of characteres in the name parameter")
        session['form_data'] = request.form.to_dict()
        return redirect(request.referrer)
    
    if len(post_subject) > 50:
        flash("You've reached the limit of characteres in the subject parameter")
        session['form_data'] = request.form.to_dict()
        return redirect(request.referrer)

    if not handler.check_banned():
        session['form_data'] = request.form.to_dict()
        return redirect(request.referrer)

    if not handler.check_timeout():
        session['form_data'] = request.form.to_dict()
        return redirect(request.referrer)

    if post_mode == "reply":
        reply_to = request.form['thread_id']
        if not handler.validate_comment():
            session['form_data'] = request.form.to_dict()
            return redirect(request.referrer)
        if not handler.handle_reply(reply_to):
            session['form_data'] = request.form.to_dict()
            return redirect(request.referrer)
    else:
        match = re.match(r'^>>(\d+)', comment)
        if match:
            reply_to = match.group(1)
            if not database_module.check_post_exist(int(reply_to)):
                reply_to = request.form.get('thread_id', '')
                if not reply_to:
                    flash("Invalid thread reference.")
                    session['form_data'] = request.form.to_dict()
                    return redirect(request.referrer)
            
            if not handler.handle_reply(reply_to):
                session['form_data'] = request.form.to_dict()
                return redirect(request.referrer)
        else:
            if not handler.validate_comment():
                session['form_data'] = request.form.to_dict()
                return redirect(request.referrer)
            if not handler.handle_post():
                session['form_data'] = request.form.to_dict()
                return redirect(request.referrer)
    
    if post_mode == "reply":
        return redirect(request.referrer)

    return redirect(f'/{board_id}/thread/{database_module.get_max_post_id()}')

@posts_bp.route('/socket.io/')
def socket_io():
    socketio_manage(request.environ, {'/': SocketIOHandler}, request=request)
