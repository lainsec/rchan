"""
Imageboard Database Module using LainDB
This module handles all database operations for an imageboard system.
"""

import datetime
import hashlib
import random
import base64
import string
import pytz
import json
import os
import io
import re
from threading import Lock
from PIL import Image, ImageDraw, ImageFont

# Initialize Lock for post ID generation
POST_LOCK = Lock()

from database_modules.sqlite_handler import SQLiteConfig

# Initialize SQLite databases
DB = SQLiteConfig.load_db('imageboard')
DB.create_table('boards', {
    'id': 'int',
    'board_uri': 'str',
    'board_name': 'str',
    'board_desc': 'str',
    'board_owner': 'str',
    'board_staffs': 'list',
    'enable_captcha': 'int',
    'board_isvisible': 'int',
    'tag': 'str',
    'require_media_approval': 'int'
})
DB.add_column('boards', 'tag')
DB.add_column('boards', 'require_media_approval')
DB.create_table('accounts', {
    'id': 'int',
    'username': 'str',
    'password': 'str',
    'role': 'str'
})
DB.create_table('posts', {
    'id': 'int',
    'user_ip': 'str',
    'post_id': 'int',
    'post_user': 'str',
    'post_subject': 'str',
    'post_date': 'str',
    'board': 'str',
    'original_content': 'str',
    'post_content': 'str',
    'post_images': 'list',
    'locked': 'int',
    'visible': 'int',
    'media_approved': 'int'
})
DB.add_column('posts', 'media_approved')
DB.create_table('pinned', {
    'id': 'int',
    'user_ip': 'str',
    'post_id': 'int',
    'post_user': 'str',
    'post_date': 'str',
    'board': 'str',
    'post_content': 'str',
    'post_images': 'list',
    'media_approved': 'int'
})
DB.add_column('pinned', 'media_approved')
DB.create_table('replies', {
    'id': 'int',
    'user_ip': 'str',
    'reply_id': 'int',
    'post_id': 'int',
    'post_user': 'str',
    'post_subject': 'str',
    'post_date': 'str',
    'content': 'str',
    'images': 'list',
    'media_approved': 'int'
})
DB.add_column('replies', 'media_approved')
DB.create_table('users', {
    'id': 'int',
    'user_ip': 'str',
    'user_role': 'str'
})

# Utility Functions
def generate_captcha():
    """Generate a custom CAPTCHA challenge."""
    # 1. Generate text (lowercase + digits)
    captcha_text = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    
    # 2. Setup Image
    width, height = 200, 80
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # 3. Draw Mosaic Background (White and Gray)
    box_size = 10
    for x in range(0, width, box_size):
        for y in range(0, height, box_size):
            if random.random() > 0.5:
                fill_color = '#e0e0e0' # Light Gray
            else:
                fill_color = 'white'
            draw.rectangle([x, y, x + box_size, y + box_size], fill=fill_color)
            
    # 4. Load Font (Comic Sans from static/css/fonts)
    # Construct path relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_path = os.path.join(base_dir, 'static', 'css', 'fonts', 'comic.ttf')
    
    try:
        font = ImageFont.truetype(font_path, 42)
    except IOError:
        # Fallback to system font if local font fails
        font_path = "/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf"
        try:
             font = ImageFont.truetype(font_path, 42)
        except IOError:
             font = ImageFont.load_default()

    # 5. Draw Text (Centered)
    # Using anchor='mm' (middle-middle) to center text bounding box relative to image center
    # This requires Pillow >= 8.0.0 (Project uses 11.0.0)
    
    cx = width / 2
    cy = height / 2
    
    draw.text((cx, cy), captcha_text, font=font, fill='black', anchor='mm')
    
    # 6. Draw Horizontal Line Cutting Through Middle of Text with Glitch Effect
    # Base line Y is cy
    line_thickness = 4
    
    prev_x = 0
    prev_y = cy
    
    step = 5
    for x in range(step, width + step, step):
        # Random vertical jitter
        y_jitter = random.randint(-1, 1)
        curr_y = cy + y_jitter
        
        # Draw segment
        draw.line((prev_x, prev_y, x, curr_y), fill='black', width=line_thickness)
        
        # Randomly add "glitch" blocks
        if random.random() < 0.05: # 5% chance
            glitch_w = random.randint(2, 6)
            glitch_h = random.randint(2, 6)
            g_x = x - random.randint(0, step)
            g_y = curr_y + random.randint(-4, 4)
            draw.rectangle([g_x, g_y, g_x + glitch_w, g_y + glitch_h], fill='black')
            
        prev_x = x
        prev_y = curr_y
    
    # 7. Save to Buffer
    image_io = io.BytesIO()
    image.save(image_io, format='PNG')
    image_base64 = base64.b64encode(image_io.getvalue()).decode('utf-8')
    
    return captcha_text, f"data:image/png;base64,{image_base64}"

def generate_tripcode(post_name, account_name, board_owner, board_staffs):
    """Generate a tripcode from post name and handle board owner tags."""
    # Handle board owner tag (##) first
    if '##' in post_name:
        existing_user = DB.query('accounts', {'username': {'==': account_name}})
        if existing_user:
            if account_name in board_staffs:
                user_role = 'Board Staff'
                post_name = post_name.replace('##', f'<span class="user_name_role">{user_role}</span>')
            if existing_user[0]['role'] == 'mod':
                user_role = 'General Moderator'
                post_name = post_name.replace('##', f'<span class="user_name_role">{user_role}</span>')
            elif existing_user[0]['role'] == 'owner':
                user_role = 'General Owner'
                post_name = post_name.replace('##', f'<span class="user_name_role">{user_role}</span>')
            elif existing_user[0]['role'] == '' and account_name == board_owner:
                user_role = 'Board Owner'
                post_name = post_name.replace('##', f'<span class="user_name_role">{user_role}</span>')
            elif existing_user[0]['role'] == '' or account_name == '':
                post_name = post_name.replace('##', '')
    
    # Then handle regular tripcode (#text)
    match = re.search(r'#(\S+)', post_name)
    if match:
        text_to_encrypt = match.group(1)
        # Skip if it was part of the board owner tag
        if text_to_encrypt != '#':
            hashed_text = hashlib.sha256(text_to_encrypt.encode('utf-8')).hexdigest()
            truncated_hash = hashed_text[:12]
            post_name = post_name.replace(f'#{text_to_encrypt}', f' <span class="tripcode">!@{truncated_hash}</span>')
    
    return post_name

def hash_password(password):
    """Hash a password with PBKDF2."""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + hashed.hex()

def verify_password(stored_password, provided_password):
    """Verify a password against its hash."""
    salt, hashed = stored_password.split(':')
    salt = bytes.fromhex(salt)
    hashed_provided = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return hashed_provided.hex() == hashed

def validate_captcha(captcha_input, captcha_text):
    """Validate CAPTCHA input."""
    return captcha_input == captcha_text

def hash_ip(ip):
    if not ip:
        return ''
    ip_str = str(ip)
    digest = hashlib.sha256(ip_str.encode('utf-8')).hexdigest()
    return digest[:12]

def get_current_datetime():
    """Get current datetime in Brazil timezone."""
    current_date_time = pytz.timezone('America/Sao_Paulo') # Change this if your country isn't Brasil.
    return datetime.datetime.now(current_date_time).strftime("%d/%m/%Y %H:%M:%S")

# Board Operations
def verify_board_captcha(board_uri):
    """Check if CAPTCHA is enabled for a board."""
    board = DB.query('boards', {'board_uri': {'==': board_uri}})
    if board and 'enable_captcha' in board[0]:
        return board[0]['enable_captcha'] == 1
    return False

def set_all_boards_captcha(option):
    """Enable/disable CAPTCHA for all boards."""
    boards = DB.find_all('boards')
    for board in boards:
        board['enable_captcha'] = 1 if option == 'enable' else 0
        DB.update('boards', board['id'], board)
    return True

def set_board_captcha(board_uri, option):
    """Enable/disable CAPTCHA for specific board."""
    boards = DB.query('boards', {'board_uri': {'==': board_uri}})
    board = boards[0]
    board['enable_captcha'] = 1 if option == 'enable' else 0
    DB.update('boards', board['id'], board)
    return True

def get_board_info(board_uri):
    """Get information about a specific board."""
    board = DB.query('boards', {'board_uri': {'==': board_uri}})
    return board[0] if board else None

def get_board_banner(board_uri):
    """Get a random banner for a board."""
    banner_folder = os.path.join('./static/imgs/banners', board_uri)
    if not os.path.exists(banner_folder):
        return None
    
    try:
        images = [f for f in os.listdir(banner_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    except Exception as e:
        print(f"Error listing images: {e}")
        return None
    
    if not images:
        return '/static/imgs/banners/default.jpg'
    
    selected_image = random.choice(images)
    return f'/static/imgs/banners/{board_uri}/{selected_image}'

def get_all_posts(include_replies=False, board_filter=None, sort_by_date=False):
    """
    Get all posts from the database, optionally filtered by board and including replies.
    Can control whether to sort by date or not.
    
    Args:
        include_replies (bool): Whether to include replies in the results
        board_filter (str): Optional board URI to filter posts by
        sort_by_date (bool): Whether to sort posts by date (newest first). Default True.
        
    Returns:
        list: List of all posts (and optionally replies) matching the criteria
    """
    try:
        # Get all main posts
        query = {}
        if board_filter:
            query['board'] = {'==': board_filter}
        
        posts = DB.query('posts', query)
        
        if include_replies:
            # Get all replies
            replies = DB.find_all('replies')
            
            # Combine posts and replies
            all_content = posts + replies
        else:
            all_content = posts
        
        # Sort by date if requested
        if sort_by_date:
            all_content.sort(key=lambda x: x['post_date'], reverse=True)
        
        return all_content
    
    except Exception as e:
        print(f"Error retrieving posts: {e}")
        return []

def get_all_boards(include_stats=False):
    """
    Get all boards from the database, optionally with statistics.
    
    Args:
        include_stats (bool): Whether to include post and thread counts for each board
        
    Returns:
        list: List of all boards, each as a dictionary with board information
    """
    try:
        boards = DB.find_all('boards')
        
        if include_stats:
            for board in boards:
                board_uri = board['board_uri']

                board['board_isvisible'] = board.get('board_isvisible', 1)
                
                # Get all posts for this board
                posts = DB.query('posts', {
                    'board': {'==': board_uri}
                })
                
                # Thread count is just the number of posts
                board['thread_count'] = len(posts)
                
                # Get reply count for each post
                reply_count = 0
                last_activity = None
                
                for post in posts:
                    # Get replies for this post
                    replies = DB.query('replies', {
                        'post_id': {'==': post['post_id']}
                    })
                    
                    reply_count += len(replies)
                    
                    # Check for last activity in replies
                    for reply in replies:
                        if not last_activity or reply['post_date'] > last_activity:
                            last_activity = reply['post_date']
                
                # Total posts is threads + replies
                board['total_posts'] = board['thread_count'] + reply_count
                
                # Check for last activity in posts
                for post in posts:
                    if not last_activity or post['post_date'] > last_activity:
                        last_activity = post['post_date']
                
                board['last_activity'] = last_activity
        
        return boards
    
    except Exception as e:
        print(f"Error retrieving boards: {e}")
        return []

def get_board_stats(board_uri):
    """
    Get detailed statistics for a specific board.
    
    Args:
        board_uri (str): The URI of the board
        
    Returns:
        dict: Dictionary containing board statistics
    """
    stats = {
        'thread_count': 0,
        'reply_count': 0,
        'total_posts': 0,
        'last_activity': None,
        'pinned_threads': 0
    }
    
    try:
        # Get thread count
        stats['thread_count'] = len(DB.query('posts', {
            'board': {'==': board_uri}
        }))
        
        # Get reply count
        thread_ids = [post['post_id'] for post in DB.query('posts', {
            'board': {'==': board_uri}
        })]
        
        if thread_ids:
            stats['reply_count'] = len(DB.query('replies', {
                'post_id': {'in': thread_ids}
            }))
        
        stats['total_posts'] = stats['thread_count'] + stats['reply_count']
        
        # Get pinned threads count
        stats['pinned_threads'] = len(DB.query('pinned', {
            'board': {'==': board_uri}
        }))
        
        # Get last activity
        last_post = DB.query('posts', {
            'board': {'==': board_uri}
        }, sort_by='post_date', sort_desc=True, limit=1)
        
        last_reply = None
        if thread_ids:
            last_reply = DB.query('replies', {
                'post_id': {'in': thread_ids}
            }, sort_by='post_date', sort_desc=True, limit=1)
        
        if last_post:
            stats['last_activity'] = last_post[0]['post_date']
        if last_reply:
            if not stats['last_activity'] or last_reply[0]['post_date'] > stats['last_activity']:
                stats['last_activity'] = last_reply[0]['post_date']
        
        return stats
    
    except Exception as e:
        print(f"Error getting stats for board {board_uri}: {e}")
        return stats

def search_boards(search_term):
    """
    Search boards by name or description.
    
    Args:
        search_term (str): Term to search for in board names and descriptions
        
    Returns:
        list: List of matching boards
    """
    try:
        # Search in board names
        name_results = DB.query('boards', {
            'board_name': {'LIKE': f'%{search_term}%'}
        })
        
        # Search in board descriptions
        desc_results = DB.query('boards', {
            'board_desc': {'LIKE': f'%{search_term}%'}
        })
        
        # Combine results and remove duplicates
        combined = name_results + desc_results
        seen = set()
        unique_results = []
        
        for board in combined:
            identifier = board['board_uri']
            if identifier not in seen:
                seen.add(identifier)
                unique_results.append(board)
        
        return unique_results
    
    except Exception as e:
        print(f"Error searching boards: {e}")
        return []

def get_popular_boards(limit=5):
    """
    Get the most active boards based on recent activity.
    
    Args:
        limit (int): Number of boards to return
        
    Returns:
        list: List of popular boards with activity stats
    """
    try:
        all_boards = get_all_boards(include_stats=True)
        
        # Filter boards with activity and sort by last activity
        active_boards = [b for b in all_boards if b.get('last_activity')]
        active_boards.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return active_boards[:limit]
    
    except Exception as e:
        print(f"Error getting popular boards: {e}")
        return []

def get_max_post_id():
    max_post_id = max([post['post_id'] for post in DB.find_all('posts')] + [0]) 
    max_reply_id = max([reply['reply_id'] for reply in DB.find_all('replies')] + [0])
    max_id = max(max_post_id, max_reply_id)
    return max_id

def get_post_info(post_id):
    """Get post information by post ID, excluding the poster's IP."""
    try:
        post_id = int(post_id)
    except (TypeError, ValueError):
        return None
    post = DB.query('posts', {'post_id': {'==': post_id}})
    replies = DB.query('replies', {'reply_id': {'==': post_id}})
    if post:
        post_copy = dict(post[0])
        post_copy.pop('user_ip', None)
        return post_copy
    elif replies:
        reply_copy = dict(replies[0])
        reply_copy.pop('user_ip', None)
        return reply_copy
    return None

def get_post_ip(post_id):
    """Get the IP address of a post or reply."""
    post_id = int(post_id)
    post = DB.query('posts', {'post_id': {'==': post_id}})
    replies = DB.query('replies', {'reply_id': {'==': post_id}})
    if post:
        return post[0].get('user_ip')
    elif replies:
        return replies[0].get('user_ip')
    return None

def create_banner_folder(board_uri):
    """Create a folder for board banners."""
    board_folder = os.path.join('./static/imgs/banners/', board_uri)
    os.makedirs(board_folder, exist_ok=True)

def add_new_board(board_uri, board_name, board_description, username, captcha_input, captcha_text, tag='Outros'):
    """Create a new board."""
    if not validate_captcha(captcha_input, captcha_text):
        return False
    
    if not board_uri.isalnum():
        return False
    
    # Reserved URIs that are used as routes in boards_bp.py
    reserved_uris = {
        'home',
        'tabuas',
        'conta',
        'registrar',
        'create'
    }
    if board_uri.lower() in reserved_uris:
        return False
    
    existing_boards = DB.query('boards', {'board_uri': {'==': board_uri}})
    if existing_boards:
        return False
    
    if len(board_uri) < 1 or len(board_name) < 1 or len(board_description) <= 3:
        return False
    
    max_board_id = max([board['id'] for board in DB.find_all('boards')] + [0])
    new_board_id = max_board_id + 1
    
    new_board = {
        'id': new_board_id,
        'board_owner': username,
        'board_staffs': [],
        'board_uri': board_uri,
        'board_name': board_name,
        'board_desc': board_description,
        'enable_captcha': 0,
        'board_isvisible': 1,
        'tag': tag,
        'require_media_approval': 0
    }
    
    DB.insert('boards', new_board)
    create_banner_folder(board_uri)
    return True

def hide_board(board_uri):
    """Hide a board."""
    board_info = get_board_info(board_uri)
    if not board_info:
        return False
    
    DB.update('boards', board_info['id'], {'board_isvisible': 0})
    return True

def unhide_board(board_uri):
    """Unhide a board."""
    board_info = get_board_info(board_uri)
    if not board_info:
        return False
    
    DB.update('boards', board_info['id'], {'board_isvisible': 1})
    return True

def edit_board_info(board_uri, new_board_owner, new_board_name, new_board_desc, new_board_tag, require_media_approval=None):
    """Edit board information."""
    board_info = get_board_info(board_uri)
    if not board_info:
        return False
    
    update_data = {
        'board_owner': new_board_owner,
        'board_name': new_board_name,
        'board_desc': new_board_desc,
        'tag': new_board_tag
    }

    if require_media_approval is not None:
        update_data['require_media_approval'] = int(require_media_approval)

    DB.update('boards', board_info['id'], update_data)
    return True

def remove_board(board_uri, username, role):
    """Remove a board."""
    board_info = get_board_info(board_uri)
    if not board_info:
        return False
    
    if board_info.get('board_owner') != username and 'mod' not in role.lower() and 'owner' not in role.lower():
        return False
    
    # Remove all posts from this board
    posts = DB.query('posts', {'board': {'==': board_uri}})
    for post in posts:
        remove_post(post['post_id'])
    
    # Remove the board
    DB.delete('boards', board_info['id'])
    return True

def add_board_staff(board_uri, username):
    """
    Add a new staff member to the board_staffs list of a board.
    Validates that the user and the board exist, and that the user
    is not already a staff member of the board.
    """

    # Check if the user exists
    users = DB.query("accounts", {"username": {"==": username}})
    if not users:
        raise ValueError(f"User '{username}' not found.")

    # Check if the board exists
    boards = DB.query("boards", {"board_uri": {"==": board_uri}})
    if not boards:
        raise ValueError(f"Board '{board_uri}' not found.")

    board = boards[0]

    # Ensure board_staffs exists and is a list
    if "board_staffs" not in board or not isinstance(board["board_staffs"], list):
        board["board_staffs"] = []

    # Check if the user is already staff for this board
    if username in board["board_staffs"]:
        raise ValueError(f"User '{username}' is already staff for board '{board_uri}'.")

    # Add the user to the board_staffs list
    board["board_staffs"].append(username)

    # Update in the database
    DB.update("boards", board["id"], board)

    return True

def remove_board_staff(board_uri, username):
    """
    Remove a staff member from the board_staffs list of a board.
    Validates that the user and the board exist, and that the user
    is currently a staff member of the board.
    """

    # Check if the user exists
    users = DB.query("accounts", {"username": {"==": username}})
    if not users:
        raise ValueError(f"User '{username}' not found.")

    # Check if the board exists
    boards = DB.query("boards", {"board_uri": {"==": board_uri}})
    if not boards:
        raise ValueError(f"Board '{board_uri}' not found.")

    board = boards[0]

    # Ensure board_staffs exists and is a list
    if "board_staffs" not in board or not isinstance(board["board_staffs"], list):
        board["board_staffs"] = []

    # Check if the user is actually a staff for this board
    if username not in board["board_staffs"]:
        raise ValueError(f"User '{username}' is not staff for board '{board_uri}'.")

    # Remove the user from the staff list
    board["board_staffs"].remove(username)

    # Update in the database
    DB.update("boards", board["id"], board)

    return True


# User Operations
def login_user(username, password):
    """Authenticate a user."""
    user = DB.query('accounts', {'username': {'==': username}})
    if user and verify_password(user[0]['password'], password):
        return True
    return False

def register_user(username, password, captcha_input, captcha_text):
    """Register a new user."""
    if not validate_captcha(captcha_input, captcha_text) or len(username) <= 3:
        return False
    
    existing_user = DB.query('accounts', {'username': {'==': username}})
    if existing_user:
        return False
    
    hashed_password = hash_password(password)
    role = 'owner' if len(DB.find_all('accounts')) == 0 else ''
    
    max_account_id = max([account['id'] for account in DB.find_all('accounts')] + [0])
    new_user = {
        'id': max_account_id + 1,
        'username': username,
        'password': hashed_password,
        'role': role
    }
    
    DB.insert('accounts', new_user)
    return True

def get_user_role(username):
    """Get a user's role."""
    user = DB.query('accounts', {'username': {'==': username}})
    return user[0]['role'] if user else None

def get_post_board(post_id):
    """Get the info from post."""
    post_id = int(post_id)
    post = DB.query('posts', {'post_id': {'==': post_id}})
    if post:
        return post[0]['board']

    reply = DB.query('replies', {'reply_id': {'==': post_id}})
    if reply:
        post = DB.query('posts', {'post_id': {'==': reply[0]['post_id']}})
        return post[0]['board'] if post else None
    
    return None

def check_user_exists(username):
    """Check if a user exists."""
    user = DB.query('accounts', {'username': {'==': username}})
    return True if user else False

def check_post_exist(post_id):
    """Verify if thread exists."""
    post = DB.query('posts', {'post_id': {'==': post_id}})
    if not post:
        reply = DB.query('replies', {'reply_id': {'==': post_id}})
        return True if reply else False
    return True

def check_replyto_exist(post_id):
    """Verify if reply_to thread exists."""
    post = DB.query('posts', {'post_id': {'==': post_id}})
    return True if post else False

# Post Operations
def bump_thread(thread_id):
    """
    Bump a thread by deleting and recreating for keep the thread new on DB.
    This brings the thread to the end of the database (making it appear first in descending order).
    
    Args:
        thread_id (int): The ID of the thread to bump
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Remove the thread from DB.
        thread = DB.query('posts', {'post_id': {'==': thread_id}})
        if not thread:
            return False
        
        thread = thread[0]
        DB.delete('posts', thread['id'])
        
        # Finally insert again.
        if 'id' in thread:
            del thread['id']
        DB.insert('posts', thread)
        
        return True
    
    except Exception as e:
        print(f"Error bumping thread {thread_id}: {e}")
        return False

def add_new_post(user_ip, account_name, board_id, post_subject, post_name, original_content, comment, embed, files):
    """Create a new post"""
    # First verify if board exists
    board = DB.query('boards', {'board_uri': {'==': board_id}})
    board_owner = board[0]['board_owner']
    board_staffs = board[0]['board_staffs']
    try:
        require_media_approval = int(board[0].get('require_media_approval', 0))
    except (ValueError, TypeError):
        require_media_approval = 0

    if not board:
        raise ValueError(f"Board '{board_id}' does not exist")
    
    with POST_LOCK:
        # Get the next post ID
        max_post_id = max([post['post_id'] for post in DB.find_all('posts')] + [0]) 
        max_reply_id = max([reply['reply_id'] for reply in DB.find_all('replies')] + [0])
        max_id = max(max_post_id, max_reply_id)
        new_post_id = max_id + 1

        # Check media approval
        media_approved = 1
        if files and require_media_approval == 1:
            is_privileged = False
            if account_name == board_owner:
                is_privileged = True
            elif account_name in board_staffs:
                is_privileged = True
            else:
                 user = DB.query('accounts', {'username': {'==': account_name}})
                 if user:
                     role = user[0]['role'].lower()
                     if 'mod' in role or 'owner' in role:
                         is_privileged = True
            
            if not is_privileged:
                media_approved = 0
            
        # Create the new post
        new_post = {
            # 'id': new_post_id, # Let SQLite handle the ID
            'user_ip': user_ip,
            'post_id': new_post_id,
            'post_user': generate_tripcode(post_name, account_name, board_owner, board_staffs),
            'post_subject': post_subject,
            'post_date': get_current_datetime(),
            'board': board_id,
            'original_content': original_content,
            'post_content': comment,
            'post_images': files, 
            'locked': 0,
            'visible': 1,
            'media_approved': media_approved
        }
        
        # Insert into database
        DB.insert('posts', new_post)
    return new_post_id

def add_new_reply(user_ip, account_name, post_subject, reply_to, post_name, comment, embed, files):
    """Add a reply to a post with multiple files."""
    existing_post = DB.query('posts', {'post_id': {'==': int(reply_to)}})
    board = DB.query('boards', {'board_uri': {'==': existing_post[0]['board']}})
    board_owner = board[0]['board_owner']
    board_staffs = board[0]['board_staffs']
    try:
        require_media_approval = int(board[0].get('require_media_approval', 0))
    except (ValueError, TypeError):
        require_media_approval = 0

    with POST_LOCK:
        max_post_id = max([post['post_id'] for post in DB.find_all('posts')] + [0]) 
        max_reply_id = max([reply['reply_id'] for reply in DB.find_all('replies')] + [0])
        max_id = max(max_post_id, max_reply_id)
        new_reply_id = max_id + 1

        # Check media approval
        media_approved = 1
        if files and require_media_approval == 1:
            is_privileged = False
            if account_name == board_owner:
                is_privileged = True
            elif account_name in board_staffs:
                is_privileged = True
            else:
                 user = DB.query('accounts', {'username': {'==': account_name}})
                 if user:
                     role = user[0]['role'].lower()
                     if 'mod' in role or 'owner' in role:
                         is_privileged = True
            
            if not is_privileged:
                media_approved = 0

        new_reply = {
            'id': new_reply_id,
            'user_ip': user_ip,
            'reply_id': new_reply_id,
            'post_id': int(reply_to),
            'post_user': generate_tripcode(post_name, account_name, board_owner, board_staffs),
            'post_subject': post_subject,
            'post_date': get_current_datetime(),
            'content': comment,
            'images': files,
            'media_approved': media_approved
        }
        if not 'sage' in post_subject.lower():
            bump_thread(int(reply_to))
        DB.insert('replies', new_reply)
    
    return new_reply_id

def get_all_registered_users(offset=0, limit=20, search_query=None):
    """Get all registered users with pagination and optional search."""
    try:
        all_users = DB.find_all('accounts')
        
        if search_query:
            search_query = search_query.lower()
            all_users = [u for u in all_users if search_query in u.get('username', '').lower()]
            
        # Sort by id
        all_users.sort(key=lambda x: x.get('id', 0)) 
        return all_users[offset:offset+limit]
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def count_all_registered_users(search_query=None):
    """Count all registered users with optional search."""
    try:
        all_users = DB.find_all('accounts')
        
        if search_query:
            search_query = search_query.lower()
            all_users = [u for u in all_users if search_query in u.get('username', '').lower()]
            
        return len(all_users)
    except Exception as e:
        print(f"Error counting users: {e}")
        return 0

def update_user_role(username, new_role):
    """Update a user's role."""
    try:
        users = DB.query('accounts', {'username': {'==': username}})
        if not users:
            return False
        user = users[0]
        DB.update('accounts', user['id'], {'role': new_role})
        return True
    except Exception as e:
        print(f"Error updating user role: {e}")
        return False


def move_thread(thread_id, new_board_uri: str):
    # Buscar thread
    thread = DB.query('posts', {'post_id': {'==': int(thread_id)}})
    if not thread:
        raise ValueError(f"Thread {thread_id} não encontrado.")

    # Verificar se o board de destino existe
    new_board = DB.query('boards', {'board_uri': {'==': new_board_uri}})
    if not new_board:
        raise ValueError(f"Board de destino {new_board_uri} não existe.")

    # Atualizar board da thread
    DB.update('posts', thread[0]['id'], {'board': new_board_uri})

    # Atualizar pinned se existir
    pinned = DB.query('pinned', {'post_id': {'==': int(thread_id)}})
    if pinned:
        for pin in pinned:
            DB.update('pinned', pin['id'], {'board': new_board_uri})

    return True


def delete_media_files(file_list, base_path, is_video=False):
    """Helper function to delete multiple media files"""
    if not file_list:
        return
    
    for filename in file_list:
        if not filename:  # Skip empty entries
            continue
            
        try:
            # Delete main file
            file_path = os.path.join(base_path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete thumbnail if it's a video
            if is_video and filename.lower().endswith(('.mp4', '.mov', '.webm')):
                thumb_name = f"thumbnail_{os.path.splitext(filename)[0]}.jpg"
                thumb_path = os.path.join(base_path, 'thumbs', thumb_name)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")

def remove_post(post_id):
    """Remove a post, its replies, and all associated media files."""
    # Remove main post and its media
    post = DB.query('posts', {'post_id': {'==': post_id}})
    if post:
        post = post[0]
        # Delete all associated media files
        delete_media_files(post.get('post_images', []), './static/post_images/', is_video=True)
        DB.delete('posts', post['id'])
    
    # Remove from pinned posts
    pinned_posts = DB.query('pinned', {'post_id': {'==': post_id}})
    for pinned in pinned_posts:
        DB.delete('pinned', pinned['id'])
    
    # Remove all replies and their media
    replies = DB.query('replies', {'post_id': {'==': post_id}})
    for reply in replies:
        delete_media_files(reply.get('images', []), './static/reply_images/')
        DB.delete('replies', reply['id'])
    
    return True

def delete_all_posts_from_user(user_ip, board_uri):
    """Remove all posts and replies made by a specific IP on a specific board."""
    # 1. Delete user's threads
    user_posts = DB.query('posts', {'user_ip': {'==': user_ip}})
    for post in user_posts:
        if post.get('board') == board_uri:
            remove_post(post['post_id'])

    # 2. Delete user's replies in other threads
    user_replies = DB.query('replies', {'user_ip': {'==': user_ip}})
    for reply in user_replies:
        # Check parent thread's board
        parent_post = DB.query('posts', {'post_id': {'==': reply['post_id']}})
        if parent_post and parent_post[0].get('board') == board_uri:
            remove_reply(reply['reply_id'])
            
    return True

def remove_reply(reply_id):
    """Remove a reply."""
    reply = DB.query('replies', {'reply_id': {'==': reply_id}})
    if reply:
        reply = reply[0]
        # Check if post has an associated image
        if reply.get('images'):
            delete_media_files(reply.get('images', []), './static/reply_images/')
        elif reply.get('image'): # Legacy check
             delete_media_files([reply.get('image')], './static/reply_images/')

        DB.delete('replies', reply['id'])

        return True

    return False

def verify_locked_thread(thread_id):
    """Check if a thread is locked."""
    post = DB.query('posts', {'post_id': {'==': thread_id}})
    return post and post[0].get('locked', 0) == 1 if post else False

def lock_thread(thread_id):
    """Lock or unlock a thread."""
    post = DB.query('posts', {'post_id': {'==': thread_id}})
    if not post:
        return False

    post_record = post[0]
    post_record['locked'] = 1 if post_record.get('locked', 0) == 0 else 0
    DB.update('posts', post_record['id'], post_record)
    return True

def pin_post(post_id):
    """Pin or unpin a post."""
    post = DB.query('posts', {'post_id': {'==': post_id}})
    if not post:
        return False
    
    post = post[0]  # Pegamos o primeiro (e único) post
    
    # Verifica se o post está visível (não pinado)
    if post.get('visible', 1) == 0:
        # Se estiver invisível (já pinado), tornamos visível novamente
        post['visible'] = 1
        pinned = DB.query('pinned', {'post_id': {'==': post_id}})
        if pinned:
            DB.delete('pinned', pinned[0]['id'])
        DB.update('posts', post['id'], post)
        return True
    
    # Se chegou aqui, vamos pinar o post
    post['visible'] = 0  # Marcamos como invisível na lista normal
    DB.update('posts', post['id'], post)
    
    # Preparamos os dados para a tabela pinned
    new_pinned = {
        'id': post['id'],
        'user_ip': post['user_ip'],
        'post_id': post['post_id'],
        'post_user': post['post_user'],
        'post_date': post['post_date'],
        'board': post['board'],
        'post_content': post['post_content'],
        'media_approved': post.get('media_approved', 1),
        # Usa post_images se existir, senão usa post_image (para compatibilidade)
        'post_images': post.get('post_images', [post.get('post_image', '')])
    }
    
    # Remove a chave post_image se existir para manter consistência
    if 'post_image' in new_pinned:
        del new_pinned['post_image']
    
    DB.insert('pinned', new_pinned)
    return True

def approve_media(post_id, is_reply=False):
    """Approve media for a post or reply."""
    table = 'replies' if is_reply else 'posts'
    id_field = 'reply_id' if is_reply else 'post_id'
    
    item = DB.query(table, {id_field: {'==': post_id}})
    if not item:
        return False
    
    item = item[0]
    item['media_approved'] = 1
    DB.update(table, item['id'], item)

    # Also update pinned table if it's a post
    if not is_reply:
        pinned_post = DB.query('pinned', {'post_id': {'==': post_id}})
        if pinned_post:
            pinned_post[0]['media_approved'] = 1
            DB.update('pinned', pinned_post[0]['id'], pinned_post[0])

    return True

def get_pending_media(board_uri=None):
    """Get all posts and replies with pending media."""
    query = {'media_approved': {'==': 0}}
    if board_uri:
        query['board'] = {'==': board_uri}
        
    posts = DB.query('posts', query)
    
    # For replies, we need to filter by board if specified
    # Replies table doesn't have 'board' column, so we need to join/check parent post
    replies_query = {'media_approved': {'==': 0}}
    pending_replies = DB.query('replies', replies_query)
    
    filtered_replies = []
    for reply in pending_replies:
        post = DB.query('posts', {'post_id': {'==': reply['post_id']}})
        if post:
            if board_uri and post[0]['board'] != board_uri:
                continue
            reply['board'] = post[0]['board'] # Add board info for display
            filtered_replies.append(reply)
            
    return {'posts': posts, 'replies': filtered_replies}

# Query Operations
def load_db_page(board_id, offset=0, limit=10):
    """Load paginated posts for a board."""
    posts = DB.query('posts', {'board': {'==': board_id}})
    return posts[::-1][offset:offset + limit]

def count_posts_in_board(board_id):
    """Count total number of posts in a board."""
    posts = DB.query('posts', {'board': {'==': board_id}})
    return len(posts)

def get_pinned_posts(board_uri):
    """Get pinned posts for a board."""
    return DB.query('pinned', {'board': {'==': board_uri}})

def get_user_boards(username):
    """Get all boards owned by a user."""
    return DB.query('boards', {'board_owner': {'==': username}})

def get_custom_themes():
    """Get available custom themes."""
    custom_css_path = './static/css/custom/'
    temas = []
    
    if os.path.exists(custom_css_path):
        for arquivo in os.listdir(custom_css_path):
            if arquivo.endswith('.css'):
                nome_sem_extensao = os.path.splitext(arquivo)[0]
                tema = {
                    "theme_name": nome_sem_extensao,
                    "theme_file": arquivo
                }
                temas.append(tema)
    else:
        print(f'Directory {custom_css_path} does not exist.')
    
    return temas

def get_all_banners(board_uri):
    """Get all banners for a board."""
    banner_folder = os.path.join('./static/imgs/banners', board_uri)
    if not os.path.exists(banner_folder):
        return []
    
    try:
        banners = [f for f in os.listdir(banner_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    except Exception as e:
        print("Error listing banners")
        return []
    
    return [f'/static/imgs/banners/{board_uri}/{banner}' for banner in banners]

def delete_board_banner(board_uri, banner_filename):
    """Delete a specific banner from a board."""
    banner_folder = os.path.join('./static/imgs/banners', board_uri)
    file_path = os.path.join(banner_folder, banner_filename)
    
    # Security check to prevent directory traversal
    if '..' in banner_filename or '/' in banner_filename or '\\' in banner_filename:
        print(f"Security check failed for banner filename: {banner_filename}")
        return False
        
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting banner: {e}")
            return False
    return False

if __name__ == '__main__':
    print('This module should not be run directly.')
