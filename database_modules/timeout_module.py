import json
import threading
from threading import Timer

def load_users():
    try:
        with open('./database/users.json','r') as users:
            database = json.load(users)
            return database
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def save_users(users):
    with open('./database/users.json', 'w') as f:
        json.dump(users, f, indent=4)

class Timer:
    def __init__(self, user_ip, timeout):
        self.user_ip = user_ip
        self.timeout = timeout
        self.timer_thread = threading.Thread(target=self.check_timeout)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def check_timeout(self):
        import time
        time.sleep(self.timeout)
        update_user_role(self.user_ip, None)

def timeout(user_ip):
    users = load_users()
    for user in users:
        if user.get('user_ip') == user_ip:
            user['user_role'] = 'timeout'
            save_users(users)
            timer = Timer(user_ip, 35)
            return
    new_user = {
        "user_ip": user_ip,
        "user_role": "timeout",
        "reason": ""
    }
    users.append(new_user)
    save_users(users)
    timer = Timer(user_ip, 35)

def update_user_role(user_ip, new_role):
    users = load_users()
    for user in users:
        if user.get('user_ip') == user_ip:
            user['user_role'] = new_role
            save_users(users)
            break