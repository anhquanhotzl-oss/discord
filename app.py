from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import requests
import time
import os

app = Flask(__name__)
CORS(app)

API_KEY = "ADMIN2026" # Bạn có thể đổi

def send_spam(token, channel_id, content, delay):
    while True:
        try:
            headers = {"Authorization": token, "Content-Type": "application/json"}
            res = requests.post(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=headers,
                json={"content": content}
            )
            if res.status_code == 429:
                time.sleep(5)
                continue
            if res.status_code in [401, 403]:
                break
            time.sleep(delay)
        except:
            time.sleep(5)

@app.route('/api/start', methods=['POST'])
def start():
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Sai API Key!"}), 401
    
    data = request.json
    threading.Thread(target=send_spam, args=(data['token'], data['channel'], data['message'], float(data['delay'])), daemon=True).start()
    return jsonify({"status": "success", "message": "Đã bắt đầu!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
