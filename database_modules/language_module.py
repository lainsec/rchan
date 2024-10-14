import json

def load_langs():
    try:
        with open('./config/languages.json','r') as langs:
            lang_db = json.load(langs)
            return lang_db
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def get_user_lang(user_lang):
    langs = load_langs()
    if user_lang in langs:
        return langs[user_lang][0]
    else:
        return langs["eng-us"][0]

if __name__ == '__main__':
    print('dont open this file alone.')