import json
import os
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['SECRET_KEY'] = 'mesh_secret_key'

@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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

# --- REPLACE THE OLD 'handle_sos' BLOCK WITH THIS ---
@socketio.on('new_alert')
def handle_alert(data):
    print(f"!!! EMERGENCY ALERT RECEIVED: {data} !!!")

    active_alerts.insert(0, data)
    if len(active_alerts) > 50:
        active_alerts.pop()

    save_to_disk()

    # ✅ Correct broadcast
    socketio.emit('broadcast_alert', data)


if __name__ == '__main__':
    print("🚀 Mesh Hub starting on http://192.168.0.100:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)