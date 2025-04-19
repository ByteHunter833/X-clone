import socketio
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
from redis import Redis
import os
import  logging





logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
CORS(app,
     cors_allowed_origins="*",
     supports_credentials=True, 
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     expose_headers=["Content-Type", "Authorization"],
     allow_headers=["Content-Type", "Authorization"]
)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# Make sure uploads folder exists and is absolute
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ulanishlar
db = SQLAlchemy(app)
redis = Redis(host='localhost', port=6379)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Update the uploaded_file route
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file: {e}")
        return "File not found", 404

from routes import *
from models import *


with app.app_context():
    db.create_all()

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

socketio = SocketIO(app, cors_allowed_origins="*")
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5050, debug=True)
