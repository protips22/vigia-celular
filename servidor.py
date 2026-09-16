from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import base64
import uuid

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

ALERT_DIR = Path('alertas')
ALERT_DIR.mkdir(exist_ok=True)
alerts = []

@app.get('/')
def home():
    return send_from_directory('.', 'index.html')

@app.get('/dashboard')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.get('/api/health')
def health():
    return jsonify({'ok': True, 'service': 'VIGÍA CELULAR', 'alerts': len(alerts)})

@app.get('/api/alerts')
def get_alerts():
    return jsonify(alerts[-100:][::-1])

@app.post('/api/alert')
def receive_alert():
    data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
    image_data = data.get('image') or data.get('photo') or data.get('screenshot')
    image_url = None

    if image_data and isinstance(image_data, str) and image_data.startswith('data:image'):
        try:
            header, encoded = image_data.split(',', 1)
            extension = 'png' if 'png' in header else 'jpg'
            filename = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:8]}.{extension}'
            path = ALERT_DIR / filename
            path.write_bytes(base64.b64decode(encoded))
            image_url = f'/alertas/{filename}'
        except Exception:
            image_url = None

    alert = {
        'id': uuid.uuid4().hex,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': data.get('type') or data.get('reason') or data.get('event') or 'Distracción detectada',
        'message': data.get('message') or data.get('detail') or 'Se detectó una posible distracción por celular.',
        'image': image_url,
    }
    alerts.append(alert)
    return jsonify({'ok': True, 'alert': alert}), 201

@app.get('/alertas/<path:filename>')
def alert_image(filename):
    return send_from_directory(ALERT_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
