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

def load_boards():
    try:
        with open('./database/boards.json','r') as boards:
            boards = json.load(boards)
            return boards
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def load_accounts():
    try:
        with open('./database/accounts.json','r') as accs:
            accounts = json.load(accs)
            return accounts
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def load_db():
    try:
        with open('./database/database.json','r') as db:
            database = json.load(db)
            return database
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def load_db_page(board_id, offset=0, limit=10):
    try:
        with open('./database/database.json', 'r') as file:
            database = json.load(file)
            filtered_posts = [post for post in database if post.get('board') == board_id]
            filtered_posts = filtered_posts[::-1]
            return filtered_posts[offset:offset + limit]
    except Exception as e:
        print(f'Ocorreu um erro ao carregar a base de dados: {e}')
        return []

def load_pinned():
    try:
        with open('./database/pinned.json','r') as pin:
            database = json.load(pin)
            return database
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def load_replies():
    try:
        with open('./database/replys.json','r') as replies:
            repl = json.load(replies)
            return repl
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def load_users():
    try:
        with open('./database/users.json','r') as users:
            database = json.load(users)
            return database
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def save_new_user(user):
    with open('./database/accounts.json', 'w') as f:
        json.dump(user, f, indent=4)

def save_new_post(post):
    with open('./database/database.json', 'w') as f:
        json.dump(post, f, indent=4)

def save_new_pinned(post):
    with open('./database/pinned.json', 'w') as f:
        json.dump(post, f, indent=4)

def save_new_reply(reply):
    with open('./database/replys.json', 'w') as f:
        json.dump(reply, f, indent=4)

def save_new_board(board):
    with open('./database/boards.json', 'w') as f:
        json.dump(board, f, indent=4)

def generate_captcha():
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    image = ImageCaptcha()
    image_data = image.generate(captcha_text)
    image_io = io.BytesIO(image_data.read())
    image_base64 = base64.b64encode(image_io.getvalue()).decode('utf-8')
    return captcha_text, f"data:image/png;base64,{image_base64}"

def generate_tripcode(post_name):
    match = re.search(r'#(\S+)', post_name)
    if match:
        text_to_encrypt = match.group(1)
        hashed_text = hashlib.sha256(text_to_encrypt.encode('utf-8')).hexdigest()
        truncated_hash = hashed_text[:12]
        post_name = post_name.replace(f'#{text_to_encrypt}', f' <span class="tripcode">!@{truncated_hash}</span>')
    return post_name

def hash_password(password):
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + hashed.hex()

def verify_password(stored_password, provided_password):
    salt, hashed = stored_password.split(':')
    salt = bytes.fromhex(salt)
    hashed_provided = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return hashed_provided.hex() == hashed

def verify_board_captcha(board_uri):
    boards = load_boards()
    for board in boards:
        if 'enable_captcha' in board:
            if board.get('enable_captcha') == 1:
                return True
            else:
                return False
        return False

def verify_locked_thread(thread_id):
    posts = load_db()
    for post in posts:
        if post.get('post_id') == thread_id:
            if 'locked' in post:
                if post.get('locked') == 1:
                    return True
                return False
            return False

def validate_captcha(captcha_input, captcha_text):
    if captcha_input != captcha_text:
       return False
    return True

def set_all_boards_captcha(option):
    boards = load_boards()
    for board in boards:
        if option == 'disable':
            board['enable_captcha'] = 0
        else:
            board['enable_captcha'] = 1
    save_new_board(boards)
    return True

def lock_thread(thread_id):
    posts = load_db()
    for post in posts:
        if post.get('post_id') == thread_id:
            if not 'locked' in post or post.get('locked') == 0:
                post['locked'] = 1
            elif post.get('locked') == 1:
                post['locked'] = 0
            save_new_post(posts)
            return True
    return False
    
def login_user(username, password):
    users = load_accounts()
    try:
        for user in users:
            if user.get('username') == username:
                if verify_password(user.get('password'), password):
                    return True
                return False
    except Exception as e:
        print(f"Erro: {e}")
        return False

def register_user(username, password, captcha_input, captcha_text):
    if not validate_captcha(captcha_input, captcha_text):
        return False
    users = load_accounts()
    if len(username) <= 3:
        return False
    for user in users:
        if user.get('username') == username:
            return False
    
    hashed_password = hash_password(password)
    
    if len(users) == 0:
        new_user = {"username": username, "password": hashed_password, "role": "owner"}
    else:
        new_user = {"username": username, "password": hashed_password, "role": ""}
    
    users.append(new_user)
    save_new_user(users)
    return True

def get_pinned_posts(board_uri):
    pinned = load_pinned()
    found_pins = []
    for pin in pinned:
        if pin.get('board') == board_uri:
            found_pins.append(pin)
            
    return found_pins

def get_user_role(username):
    users = load_accounts()
    try:
        for user in users:
            if user.get('username') == username:
                role = user.get('role')
                return role
    except:
        return False

def get_user_boards(username):
    boards = load_boards()
    user_boards = []
    try:
        for board in boards:
            if 'board_owner' in board:
                if board.get('board_owner') == username:
                    user_boards.append(board)
        return user_boards
    except:
        return False

def get_board_info(board_uri):
    boards = load_boards()
    for board in boards:
        if board.get('board_uri') == board_uri:
            return board

def get_board_banner(board_uri):
    banner_folder = os.path.join('./static/imgs/banners', board_uri)
    if not os.path.exists(banner_folder):
        return None  
    try:
        images = [f for f in os.listdir(banner_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    except Exception as e:
        print(f"Erro ao listar imagens: {e}")
        return None 
    if not images:
        return '/static/imgs/banners/default.jpg'
    selected_image = random.choice(images)
    return f'/static/imgs/banners/{board_uri}/{selected_image}'

def get_all_banners(board_uri):
    banner_folder = os.path.join('./static/imgs/banners', board_uri)
    if not os.path.exists(banner_folder):
        return []
    try:
        banners = [f for f in os.listdir(banner_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    except Exception as e:
        print("Erro ao listar banners")
        return [] 
    return [os.path.join('/static/imgs/banners', board_uri, banner) for banner in banners]

def check_timeout_user(user_ip):
    users = load_users()
    for user in users:
        if user.get('user_ip') == user_ip:
            role = user.get('user_role')
            if role == 'timeout':
                return True
                break
            return False
            break
    return False

def check_post_exist(reply_to):
    posts = load_db()
    if reply_to in posts:
        return True
    return False

def check_board(board_uri):
    boards = load_boards()
    for board in boards:
        if board.get('board_uri') == board_uri:
            return True
            break
    return False

def check_banned_user(user_ip):
    users = load_users()
    for user in users:
        if user.get('user_ip') == user_ip:
            role = user.get('user_role')
            if role == 'banned':
                return True
            return False
            break     

def add_new_post(user_ip,board_id, post_name, comment, embed, file):
    posts = load_db()
    replies = load_replies()
    fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
    agora = datetime.datetime.now(fuso_horario_brasilia)
    formatado = agora.strftime("%d/%m/%Y %H:%M:%S")
    max_post_id = max((post['post_id'] for post in posts), default=0)
    max_reply_id = max((reply['reply_id'] for reply in replies), default=0)
    maior_id = max(max_post_id, max_reply_id)
    new_post_id = maior_id + 1
    new_post = {
        "user_ip": user_ip,
        "post_id": new_post_id,
        "post_user": generate_tripcode(post_name),
        "post_date": str(formatado),
        "board": board_id,
        "post_content": comment,
        "post_image": file
    }
    posts.append(new_post)
    save_new_post(posts)

def add_new_reply(user_ip,reply_to, post_name, comment, embed, file):
    posts = load_db()
    replies = load_replies()
    fuso_horario_brasilia = pytz.timezone('America/Sao_Paulo')
    agora = datetime.datetime.now(fuso_horario_brasilia)
    formatado = agora.strftime("%d/%m/%Y %H:%M:%S")
    max_post_id = max((post['post_id'] for post in posts), default=0)
    max_reply_id = max((reply['reply_id'] for reply in replies), default=0)
    maior_id = max(max_post_id, max_reply_id)
    new_post_id = maior_id + 1
    new_reply = {
        "user_ip": user_ip,
        "reply_id": new_post_id,
        "post_id": int(reply_to),
        "post_user": generate_tripcode(post_name),
        "post_date": str(formatado),
        "content": comment,
        "image": file
    }
    replies.append(new_reply)
    save_new_reply(replies)
    post_to_move = next((p for p in posts if p['post_id'] == int(reply_to)), None)
    if post_to_move:
        posts.remove(post_to_move)
        posts.append(post_to_move)
        save_new_post(posts)

def remove_post(post_id):
    posts = load_db()
    pinned = load_pinned()
    replies = load_replies()
    for post in posts:
        if post.get('post_id') == post_id:
            posts.remove(post)
            save_new_post(posts)
            for reply in replies:
                if reply.get('post_id') == post_id:
                    replies.remove(reply)
            save_new_reply(replies)
            for pin in pinned:
                if pin.get('post_id') == post.get('post_id'):
                    pinned.remove(pin)
            save_new_pinned(pinned)
            return True
            break

def remove_reply(reply_id):
    replies = load_replies()
    for reply in replies:
        if reply.get('reply_id') == reply_id:
            replies.remove(reply)
            save_new_reply(replies)
            return True
            break

def create_banner_folder(board_uri):
    board_folder = os.path.join('./static/imgs/banners/', board_uri)
    os.makedirs(board_folder, exist_ok=True)

def add_new_board(board_uri, board_name, board_description, username, captcha_input, captcha_text):
    if not validate_captcha(captcha_input, captcha_text):
        return False
    boards = load_boards()
    for board in boards:
        if board.get('uri') == board_uri or board.get('board_name') == board_name:
            return False
    if len(board_uri) < 1:
        return False
    if len(board_name) < 1:
        return False
    if len(board_description) <= 3:
        return False
    new_board = {
        "board_owner": username,
        "board_uri": board_uri,
        "board_name": board_name,
        "board_desc": board_description
    }
    boards.append(new_board)
    save_new_board(boards)
    create_banner_folder(board_uri)
    return True

def remove_board(board_uri, username, role):
    board_info = get_board_info(board_uri)
    boards = load_boards()
    if board_info.get('board_owner') == username or 'mod' in role.lower() or 'owner' in role.lower():
        posts = load_db()
        for post in posts:
            if post.get('board') == board_uri:
                remove_post(post.get('post_id'))
        for board in boards:
            if board.get('board_uri') == board_uri:
                boards.remove(board)
        save_new_board(boards)
        return True
    return False

def pin_post(post_id):
    posts = load_db()
    pinned = load_pinned()
    for post in posts:
        if post.get('post_id') == post_id:
            if 'visible' in post:
                if post.get('visible') == 0:
                    post['visible'] = 1
                    for pin in pinned:
                        if pin.get('post_id') == post.get('post_id'):
                            pinned.remove(pin)
                            save_new_post(posts)
                            save_new_pinned(pinned)
                            return True
            post['visible'] = 0
            new_pinned = {
                "user_ip": post.get('user_ip'),
                "post_id": post.get('post_id'),
                "post_user": post.get('post_user'),
                "post_date": post.get('post_date'),
                "board": post.get('board'),
                "post_content": post.get('post_content'),
                "post_image": post.get('post_image')
            }
            save_new_post(posts)
            pinned.append(new_pinned)
            save_new_pinned(pinned)
            return True
    return False



if __name__ == '__main__':
    print('dont open this file alone.')
