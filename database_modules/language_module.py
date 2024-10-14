import json

def load_langs():
    try:
        with open('./config/languages.json','r') as langs:
            lang_db = json.load(langs)
            return lang_db
    except:
        print('Ocorreu um erro ao carregar a base de dados.')

def save_new_lang(lang):
    with open('./config/languages.json', 'w') as f:
        json.dump(lang, f, indent=4)

def change_general_language(new_lang):
    languages = load_langs()
    if new_lang in languages:
        lang_content = languages[new_lang]
        if 'default' in languages:
            del languages['default']
        languages["default"] = lang_content
        save_new_lang(languages)
        return True
    else:
        return False

def get_user_lang(user_lang):
    langs = load_langs()
    if user_lang in langs:
        return langs[user_lang][0]
    else:
        return langs["default"][0]

if __name__ == '__main__':
    print('dont open this file alone.')
