import json
import os
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['SECRET_KEY'] = 'mesh_secret_key'
# Setting manage_session=False can help with stability in mesh networks
socketio = SocketIO(app, cors_allowed_origins="*")

# --- DATA PERSISTENCE LAYER ---
DATA_FILE = 'mesh_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get('chat', []), data.get('alerts', [])
    return [], []

def save_to_disk():
    with open(DATA_FILE, 'w') as f:
        json.dump({'chat': chat_history, 'alerts': active_alerts}, f)

chat_history, active_alerts = load_data()

# --- ROUTES ---
@app.route('/')
def index():
    return app.send_static_file('index.html')

# --- SOCKET EVENTS ---
@socketio.on('connect')
def handle_connect():
    print("New device joined the Mesh Network")
    # Send existing data so the new user isn't looking at a blank screen
    emit('init_data', {'chatHistory': chat_history, 'activeAlerts': active_alerts})

@socketio.on('new_message')
def handle_message(data):
    # Expected data: {'text': '...', 'user': '...'}
    chat_history.append(data)
    save_to_disk()
    emit('broadcast_message', data, broadcast=True)

@socketio.on('new_sos')
def handle_sos(data):
    # Expected data: {'type': 'Medical/Fire/Food', 'details': '...', 'location': '...'}
    active_alerts.insert(0, data)
    save_to_disk()
    emit('broadcast_sos', data, broadcast=True)

if __name__ == '__main__':
    print("🚀 Mesh Hub starting on http://192.168.0.100:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)