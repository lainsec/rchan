from flask import current_app, Blueprint, render_template, redirect, request, flash, session, make_response
from database_modules import database_module, moderation_module, formatting, language_module
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from PIL import Image, ImageOps
import magic
import uuid
import cv2
import re
import os
import json

# Blueprint register
posts_bp = Blueprint('posts', __name__)
socketio = SocketIO()
# Post handling class
class PostHandler:
    def __init__(self, socketio, user_ip, post_mode, post_name, post_subject, board_id, comment, embed, captcha_input, cookie_ip=None, thread_id=None):
        self.socketio = socketio
        self.user_ip = user_ip
        self.cookie_ip = cookie_ip
        self.account_name = '' if not 'username' in session else session['username']
        self.post_mode = post_mode

        board_info = database_module.get_board_info(board_id)
        try:
            allow_name_raw = board_info.get('allow_name', 1) if board_info else 1
            allow_name = int(allow_name_raw)
        except (ValueError, TypeError):
            allow_name = 1

        username = self.account_name
        roles = database_module.get_user_role(username) if username else None
        roles_lower = roles.lower() if roles else ''

        board_default_name = ''
        if board_info:
            board_default_name = board_info.get('default_poster_name') or ''
            board_owner = board_info.get('board_owner')
            board_staffs = board_info.get('board_staffs', [])
        else:
            board_owner = None
            board_staffs = []

        chan_default_name = "Anonymous"
        try:
            chan_config_manager = moderation_module.ChanConfigManager()
            chan_config = chan_config_manager.get_config()
            chan_default_name = chan_config.get('default_poster_name', "Anonymous") or "Anonymous"
        except Exception:
            chan_default_name = "Anonymous"

        is_global_admin = 'owner' in roles_lower or 'mod' in roles_lower
        is_board_owner = bool(username and board_owner and username == board_owner)
        is_board_staff = bool(username and username in board_staffs)
        is_privileged_for_name = is_global_admin or is_board_owner or is_board_staff

        raw_post_name = post_name or ''

        if allow_name or is_privileged_for_name:
            if raw_post_name.strip():
                effective_name = raw_post_name
            else:
                effective_name = board_default_name or chan_default_name
        else:
            effective_name = board_default_name or chan_default_name

        self.post_name = formatting.escape_html_post_info(effective_name)
        self.post_subject = formatting.escape_html_post_info(post_subject)
        self.board_id = board_id
        self.thread_id = thread_id
        self.original_content = comment
        try:
            self.current_post_id = database_module.get_max_post_id() + 1
        except Exception:
            self.current_post_id = None
        self.comment = formatting.format_comment(
            comment,
            current_post_id=self.current_post_id,
            current_thread_id=self.thread_id
        )
        self.embed = embed
        self.captcha_input = captcha_input
        # Apply word filters
        try:
            filter_manager = moderation_module.WordFilterManager()
            self.original_content = filter_manager.apply_filters(self.original_content)
            self.comment = filter_manager.apply_filters(self.comment)
            self.post_subject = filter_manager.apply_filters(self.post_subject)
        except Exception as e:
            print(f"Word filter error: {e}")
    # Init the managers    
    timeout_manager = moderation_module.TimeoutManager()
    ban_manager = moderation_module.BanManager()
    # Check if the user is banned
    def check_banned(self):
        lang = language_module.get_user_lang('default')
        banned_current = self.ban_manager.is_banned(self.user_ip)
        banned_cookie = {'is_banned': False}

        if self.cookie_ip:
            banned_cookie = self.ban_manager.is_banned(self.cookie_ip)

            if (
                banned_cookie.get('is_banned', False)
                and not banned_current.get('is_banned', False)
                and self.cookie_ip != self.user_ip
            ):
                boards = banned_cookie.get('boards', [])
                if banned_cookie.get('is_permanent'):
                    duration_seconds = None
                else:
                    end_time = banned_cookie.get('end_time')
                    try:
                        remaining = (end_time - datetime.now()).total_seconds()
                    except Exception:
                        remaining = 0
                    duration_seconds = None if remaining <= 0 else int(remaining)

                self.ban_manager.ban_user(
                    self.user_ip,
                    duration_seconds=duration_seconds,
                    boards=boards,
                    reason="Evasor.",
                    moderator="System",
                )
                banned_current = self.ban_manager.is_banned(self.user_ip)

        for status in (banned_current, banned_cookie):
            if not status.get('is_banned', False):
                continue
            boards = status.get('boards')
            if boards is None or boards == [] or None in boards:
                flash(lang["flash-banned-from-board"].format(reason=status.get('reason')))
                return False
            if self.board_id in boards:
                flash(lang["flash-banned-from-board"].format(reason=status.get('reason')))
                return False
        return True
    # Check if the user is in timeout
    def check_timeout(self):
        timeout_status = self.timeout_manager.check_timeout(self.user_ip)
        if timeout_status.get('is_timeout', False):
            lang = language_module.get_user_lang('default')
            flash(lang["flash-timeout-wait"])
            return False
        return True
    # Validate the comment length and content
    def validate_comment(self):
        if len(self.comment) >= 20000:
            lang = language_module.get_user_lang('default')
            flash(lang["flash-comment-length-limit"])
            return False
        if self.comment == '':
            lang = language_module.get_user_lang('default')
            flash(lang["flash-comment-required"])
            return False
        return True
    # Process uploaded files
    def process_uploaded_files(self, upload_folder, is_thread=False):
        files = request.files.getlist('fileInput')
        saved_files = []
        thumb_paths = []

        raw_options = request.form.get('fileOptions')
        file_options = []
        if raw_options:
            try:
                file_options = json.loads(raw_options)
            except Exception:
                file_options = []

        def sanitize_uuid(value):
            if not isinstance(value, str):
                return None
            value = value.strip()
            if not value:
                return None
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value):
                return None
            return value

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

        lang = language_module.get_user_lang('default')
        for index, file in enumerate(files):
            if file.filename != '' and file.filename.lower().endswith(('.jpeg', '.jpg', '.mov', '.gif', '.png', '.webp', '.webm', '.mp4')):
                # Verify the real type of the content
                file_head = file.stream.read(2048)  # Read the first bytes
                mime_type = magic.from_buffer(file_head, mime=True)
                file.stream.seek(0)  # Go to the start to save

                if mime_type not in allowed_mime_types:
                    flash(lang["flash-invalid-file-type"])
                    return [], []

                original_filename = os.path.basename(file.filename)
                _, ext = os.path.splitext(original_filename)

                base = uuid.uuid4().hex
                filename = f"{base}{ext.lower()}"

                if index < len(file_options):
                    opts = file_options[index]
                    if isinstance(opts, dict):
                        spoiler = bool(opts.get('spoiler'))
                        strip_name = bool(opts.get('strip'))
                        uuid_value = sanitize_uuid(opts.get('uuid'))
                        if strip_name and uuid_value:
                            if spoiler:
                                base = f"spoiler-{uuid_value}"
                            else:
                                base = uuid_value
                        elif spoiler:
                            base = f"spoiler-{base}"

                filename = f"{base}{ext}"
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
        lang = language_module.get_user_lang('default')
        if not database_module.check_replyto_exist(int(reply_to)):
            flash(lang["flash-thread-not-exist"])
            return False
        # Check if the thread is locked
        if database_module.verify_locked_thread(int(reply_to)):
            flash(lang["flash-thread-locked"])
            return False
        # check if the captcha is correct
        if database_module.verify_board_captcha(self.board_id):
            if not database_module.validate_captcha(self.captcha_input, session["captcha_text"]):
                flash(lang["flash-invalid-captcha"])
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
        
        media_approved = self.get_media_approval_status(bool(saved_files))
        
        self.socketio.emit('nova_postagem', {
            'type': 'New Reply',
            'post': {
                'id': database_module.get_max_post_id() + 1,
                'thread_id': reply_to,
                'name': f'{display_name}{tripcode_html}',
                'subject': self.post_subject,
                'content': self.comment,
                'files': saved_files,
                'media_approved': media_approved,
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
    def get_media_approval_status(self, has_files):
        if not has_files:
            return 1
            
        board = database_module.DB.query('boards', {'board_uri': {'==': self.board_id}})
        if not board:
            return 1
            
        try:
            require_media_approval = int(board[0].get('require_media_approval', 0))
        except (ValueError, TypeError):
            require_media_approval = 0
            
        if require_media_approval == 0:
            return 1
            
        # Check privileges
        board_owner = board[0]['board_owner']
        board_staffs = board[0]['board_staffs']
        
        if self.account_name == board_owner:
            return 1
        if self.account_name in board_staffs:
            return 1
            
        user = database_module.DB.query('accounts', {'username': {'==': self.account_name}})
        if user:
            role = user[0]['role'].lower()
            if 'mod' in role or 'owner' in role:
                return 1
                
        return 0

    # Handle new thread posts
    def handle_post(self):
        lang = language_module.get_user_lang('default')
        if database_module.verify_board_captcha(self.board_id):
            if not database_module.validate_captcha(self.captcha_input, session["captcha_text"]):
                flash(lang["flash-invalid-captcha"])
                return False
        
        upload_folder = './static/post_images/'
        os.makedirs(upload_folder, exist_ok=True)
        
        saved_files, thumb_paths = self.process_uploaded_files(upload_folder, is_thread=True)
        
        # Process embed
        embed_file = self.process_embed()
        if embed_file:
            saved_files.append(embed_file)
        
        if not saved_files:
            flash(lang["flash-thread-requires-media"])
            return False
        name_parts = self.post_name.split('#', 1)
        display_name = name_parts[0]
        tripcode_html = ''
        if len(name_parts) > 1:
            tripcode_html = f' <span class="tripcode">[tripcode protected]</span>'
        
        media_approved = self.get_media_approval_status(bool(saved_files))
        
        self.socketio.emit('nova_postagem', {
            'type': 'New Thread',
            'post': {
                'id': database_module.get_max_post_id() + 1,
                'name': f'{display_name}{tripcode_html}',
                'subject': self.post_subject,
                'content': self.comment,
                'files': saved_files,
                'media_approved': media_approved,
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
    cookie_ip = request.cookies.get('user_ip')
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
        lang = language_module.get_user_lang('default')
        flash(lang["flash-html-tags-not-allowed"])
        session['form_data'] = request.form.to_dict()
        return redirect(request.referrer)

    thread_id = None
    if post_mode == "reply":
        thread_id = request.form.get('thread_id')

    handler = PostHandler(socketio, user_ip, post_mode, post_name, post_subject, board_id, comment, embed, captcha_input, cookie_ip, thread_id)
    
    if len(post_name) > 40:
        lang = language_module.get_user_lang('default')
        flash(lang["flash-name-length-limit"])
        session['form_data'] = request.form.to_dict()
        return redirect(request.referrer)
    
    if len(post_subject) > 50:
        lang = language_module.get_user_lang('default')
        flash(lang["flash-subject-length-limit"])
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
        try:
            allowlist_manager = moderation_module.ThreadCreationAllowlistManager()
            allowlist_manager.allow_for_hours(user_ip, hours=2)
        except Exception as e:
            print(f"Allowlist error on reply: {e}")
    else:
        lang = language_module.get_user_lang('default')
        match = re.match(r'^>>(\d+)', comment)
        if match:
            reply_to = match.group(1)
            if not database_module.check_post_exist(int(reply_to)):
                reply_to = request.form.get('thread_id', '')
                if not reply_to:
                    flash(lang["flash-invalid-thread-reference"])
                    session['form_data'] = request.form.to_dict()
                    return redirect(request.referrer)
            
            if not handler.handle_reply(reply_to):
                session['form_data'] = request.form.to_dict()
                return redirect(request.referrer)
            try:
                allowlist_manager = moderation_module.ThreadCreationAllowlistManager()
                allowlist_manager.allow_for_hours(user_ip, hours=2)
            except Exception as e:
                print(f"Allowlist error on reply: {e}")
        else:
            try:
                allowlist_manager = moderation_module.ThreadCreationAllowlistManager()
                if database_module.count_posts_in_board(board_id) > 0 and not allowlist_manager.is_ip_allowed(user_ip):
                    flash(lang["flash-thread-reply-before-post"])
                    session['form_data'] = request.form.to_dict()
                    return redirect(request.referrer)
            except Exception as e:
                print(f"Allowlist error on thread creation check: {e}")
            if not handler.validate_comment():
                session['form_data'] = request.form.to_dict()
                return redirect(request.referrer)
            if not handler.handle_post():
                session['form_data'] = request.form.to_dict()
                return redirect(request.referrer)
    
    if post_mode == "reply":
        response = redirect(request.referrer)
    else:
        response = redirect(f'/{board_id}/thread/{database_module.get_max_post_id()}')
    if user_ip:
        response.set_cookie('user_ip', user_ip, max_age=60 * 60 * 24 * 365, httponly=True, samesite='Lax')
    return response

@posts_bp.route('/socket.io/')
def socket_io():
    socketio_manage(request.environ, {'/': SocketIOHandler}, request=request)
