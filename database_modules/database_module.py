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

def save_new_post(post):
    with open('./database/database.json', 'w') as f:
        json.dump(post, f, indent=4)

def save_new_reply(reply):
    with open('./database/replys.json', 'w') as f:
        json.dump(reply, f, indent=4)

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

def check_board(board_name):
    boards = load_boards()
    for board in boards:
        if board.get('board_name') == board_name:
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

if __name__ == '__main__':
    print('dont open this file alone.')
