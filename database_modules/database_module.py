import json
import random
import datetime
import pytz

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

def save_new_reply(reply):
    with open('./database/replys.json', 'w') as f:
        json.dump(reply, f, indent=4)

def save_new_board(board):
    with open('./database/boards.json', 'w') as f:
        json.dump(board, f, indent=4)

def login_user(username,password):
    users = load_accounts()
    try:
        for user in users:
            if user.get('username') == username:
                if user.get('password') == password:
                    return True
                return False
    except:
        return False

def register_user(username,password):
    users = load_accounts()
    if len(username) <= 3:
        return False
    for user in users:
        if user.get('username') == username:
            return False
            break
    new_user = {"username": username, "password": password, "role": ""}
    users.append(new_user)
    save_new_user(users)
    return True

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
                    user_boards.append(board.get('board_name'))
        return user_boards
    except:
        return False

def get_board_info(board_uri):
    boards = load_boards()
    for board in boards:
        if board.get('board_uri') == board_uri:
            return board

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
    new_post = {
        "user_ip": user_ip,
        "post_id": len(posts) + len(replies) + 1,
        "post_user": post_name,
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
    new_reply = {
        "user_ip": user_ip,
        "reply_id": len(posts) + len(replies) + 1,
        "post_id": int(reply_to),
        "post_user": post_name,
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

def add_new_board(board_uri, board_name, board_description, username):
    boards = load_boards()
    for board in boards:
        if board.get('uri') == board_uri or board.get('board_name') == board_name:
            return False
    if len(board_uri) <= 3:
        return False
    if len(board_name) <= 3:
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
    return True

if __name__ == '__main__':
    print('dont open this file alone.')
