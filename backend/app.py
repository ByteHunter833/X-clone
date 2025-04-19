import socketio
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
from redis import Redis
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS sozlamalari (Flask-CORS uchun)
CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     expose_headers=["Content-Type", "Authorization"], allow_headers=["Content-Type", "Authorization"])

# Database sozlamalari
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Uploads papkasi
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ulanishlar
db = SQLAlchemy(app)
redis = Redis(host='localhost', port=6379)

# Redis ulanishini test qilish
try:
    redis.ping()
    logger.info("Redis connection successful")
except Exception as e:
    logger.error(f"Redis connection failed: {str(e)}")

# SocketIO ob'ekti
socketio = SocketIO(app, cors_allowed_origins="*")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        return "File not found", 404

# Routes va modellarni import qilish
from routes import *
from models import *

# Database jadvallarini yaratish
with app.app_context():
    db.create_all()



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5050, debug=True)