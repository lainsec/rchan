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
from captcha.image import ImageCaptcha
from laindb.laindb import Lainconfig

# Initialize LainDB databases
DB = Lainconfig.load_db('imageboard')
DB.create_table('boards', {
    'id': 'int',
    'board_uri': 'str',
    'board_name': 'str',
    'board_desc': 'str',
    'board_owner': 'str',
    'enable_captcha': 'int',
    'board_isvisible': 'int'
})
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
    'visible': 'int'
})
DB.create_table('pinned', {
    'id': 'int',
    'user_ip': 'str',
    'post_id': 'int',
    'post_user': 'str',
    'post_date': 'str',
    'board': 'str',
    'post_content': 'str',
    'post_images': 'list'
})
DB.create_table('replies', {
    'id': 'int',
    'user_ip': 'str',
    'reply_id': 'int',
    'post_id': 'int',
    'post_user': 'str',
    'post_subject': 'str',
    'post_date': 'str',
    'content': 'str',
    'images': 'list'
})
DB.create_table('users', {
    'id': 'int',
    'user_ip': 'str',
    'user_role': 'str'
})

# Utility Functions
def generate_captcha():
    """Generate a CAPTCHA challenge."""
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    image = ImageCaptcha()
    image_data = image.generate(captcha_text)
    image_io = io.BytesIO(image_data.read())
    image_base64 = base64.b64encode(image_io.getvalue()).decode('utf-8')
    return captcha_text, f"data:image/png;base64,{image_base64}"

def generate_tripcode(post_name, account_name, board_owner):
    """Generate a tripcode from post name and handle board owner tags."""
    # Handle board owner tag (##) first
    if '##' in post_name:
        existing_user = DB.query('accounts', {'username': {'==': account_name}})
        if existing_user:
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

def create_banner_folder(board_uri):
    """Create a folder for board banners."""
    board_folder = os.path.join('./static/imgs/banners/', board_uri)
    os.makedirs(board_folder, exist_ok=True)

def add_new_board(board_uri, board_name, board_description, username, captcha_input, captcha_text):
    """Create a new board."""
    if not validate_captcha(captcha_input, captcha_text):
        return False
    
    if not board_uri.isalnum():
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
        'board_uri': board_uri,
        'board_name': board_name,
        'board_desc': board_description,
        'enable_captcha': 0,
        'board_isvisible': 1
    }
    
    DB.insert('boards', new_board)
    create_banner_folder(board_uri)
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

def get_post_info(post_id):
    """Get the info from post."""
    post_id = int(post_id)
    post = DB.query('posts', {'post_id': {'==': post_id}})
    if not post:
        reply = DB.query('replies', {'reply_id': {'==': post_id}})
        return reply[0]
    return post[0]

def get_post_board(post_id):
    """Get the info from post."""
    post_id = int(post_id)
    post = DB.query('posts', {'post_id': {'==': post_id}})
    if not post:
        reply = DB.query('replies', {'reply_id': {'==': post_id}})
        post = DB.query('posts', {'post_id': {'==': reply[0]['post_id']}})
        return post[0]['board'] if post else None
    return post[0]['board'] if post else None

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
        DB.delete('posts', thread_id)
        
        # Finally insert again.
        DB.insert('posts', thread)
        
        return True
    
    except Exception as e:
        print(f"Error bumping thread {thread_id}: {e}")
        return False

def add_new_post(user_ip, account_name, board_id, post_subject, post_name, original_content, comment, embed, files):
    """Create a new post"""
    # First verify if board exists
    print(board_id)
    board = DB.query('boards', {'board_uri': {'==': board_id}})
    board_owner = board[0]['board_owner']
    if not board:
        raise ValueError(f"Board '{board_id}' does not exist")
    
    # Get the next post ID
    max_post_id = max([post['post_id'] for post in DB.find_all('posts')] + [0]) 
    max_reply_id = max([reply['reply_id'] for reply in DB.find_all('replies')] + [0])
    max_id = max(max_post_id, max_reply_id)
    new_post_id = max_id + 1

    # Create the new post
    new_post = {
        'id': new_post_id,
        'user_ip': user_ip,
        'post_id': new_post_id,
        'post_user': generate_tripcode(post_name, account_name, board_owner),
        'post_subject': post_subject,
        'post_date': get_current_datetime(),
        'board': board_id,
        'original_content': original_content,
        'post_content': comment,
        'post_images': files, 
        'locked': 0,
        'visible': 1
    }
    
    # Insert into database
    DB.insert('posts', new_post)
    return new_post_id

def add_new_reply(user_ip, account_name, post_subject, reply_to, post_name, comment, embed, files):
    """Add a reply to a post with multiple files."""
    existing_post = DB.query('posts', {'post_id': {'==': int(reply_to)}})
    board = DB.query('boards', {'board_uri': {'==': existing_post[0]['board']}})
    board_owner = board[0]['board_owner']

    max_post_id = max([post['post_id'] for post in DB.find_all('posts')] + [0]) 
    max_reply_id = max([reply['reply_id'] for reply in DB.find_all('replies')] + [0])
    max_id = max(max_post_id, max_reply_id)
    new_reply_id = max_id + 1
    new_reply = {
        'id': new_reply_id,
        'user_ip': user_ip,
        'reply_id': new_reply_id,
        'post_id': int(reply_to),
        'post_user': generate_tripcode(post_name, account_name, board_owner),
        'post_subject': post_subject,
        'post_date': get_current_datetime(),
        'content': comment,
        'images': files 
    }
    
    bump_thread(int(reply_to))
    DB.insert('replies', new_reply)
    
    return new_reply_id

def remove_post(post_id):
    """Remove a post, its replies, and all associated media files."""
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

    # Remove main post and its media
    post = DB.query('posts', {'post_id': {'==': post_id}})
    if post:
        post = post[0]
        # Delete all associated media files
        delete_media_files(post.get('post_images', []), './static/post_images/', is_video=True)
        DB.delete('posts', post_id)
    
    # Remove from pinned posts
    DB.delete('pinned', post_id)
    
    # Remove all replies and their media
    replies = DB.query('replies', {'post_id': {'==': post_id}})
    for reply in replies:
        delete_media_files(reply.get('images', []), './static/reply_images/')
        DB.delete('replies', reply['reply_id'])
    
    return True

def remove_reply(reply_id):
    """Remove a reply."""
    reply = DB.query('replies', {'reply_id': {'==': reply_id}})
    if reply:
        # Check if post has an associated image
        if reply[0].get('image'):
            image_path = os.path.join('./static/reply_images/', reply[0]['image'])
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {e}")

        DB.delete('replies', reply_id)

        return True

    return False

def verify_locked_thread(thread_id):
    """Check if a thread is locked."""
    post = DB.query('posts', {'post_id': {'==': thread_id}})
    return post and post[0].get('locked', 0) == 1 if post else False

def lock_thread(thread_id):
    """Lock or unlock a thread."""
    post = DB.query('posts', {'post_id': {'==': thread_id}})
    if post:
        post[0]['locked'] = 1 if post[0].get('locked', 0) == 0 else 0
        DB.update('posts', thread_id, post[0])
        return True
    return False

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
            DB.delete('pinned', post_id)
        DB.update('posts', post_id, post)
        return True
    
    # Se chegou aqui, vamos pinar o post
    post['visible'] = 0  # Marcamos como invisível na lista normal
    DB.update('posts', post_id, post)
    
    # Preparamos os dados para a tabela pinned
    new_pinned = {
        'id': post['id'],
        'user_ip': post['user_ip'],
        'post_id': post['post_id'],
        'post_user': post['post_user'],
        'post_date': post['post_date'],
        'board': post['board'],
        'post_content': post['post_content'],
        # Usa post_images se existir, senão usa post_image (para compatibilidade)
        'post_images': post.get('post_images', [post.get('post_image', '')])
    }
    
    # Remove a chave post_image se existir para manter consistência
    if 'post_image' in new_pinned:
        del new_pinned['post_image']
    
    DB.insert('pinned', new_pinned)
    return True

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
    
    return [os.path.join('/static/imgs/banners', board_uri, banner) for banner in banners]

if __name__ == '__main__':
    print('This module should not be run directly.')
