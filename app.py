#imports.
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_socketio import SocketIO
from blueprints.posts_bp import posts_bp
from blueprints.boards_bp import boards_bp
from blueprints.auth_bp import auth_bp
#app configuration.
app = Flask(__name__)
socketio = SocketIO(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = 'secret-key-here'

app.register_blueprint(posts_bp,socketio=socketio)
app.register_blueprint(boards_bp)
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    #run with socketIO for real-time features.
    socketio.run(app, port=3000, debug=True, allow_unsafe_werkzeug=True)
