from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import requests
import time
import os

app = Flask(__name__, static_folder='.')
CORS(app)

API_KEY = "ADMIN2026" # Mật khẩu của bạn

def send_spam(token, channel_id, content, delay):
    count = 0
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
            if res.status_code == 401 or res.status_code == 403:
                print("[LỖI] Token chết, dừng spam.")
                break
            
            if res.status_code == 200:
                count += 1
                print(f"[OK] Đã gửi {count} tin nhắn vào kênh {channel_id}")
                
            time.sleep(delay)
        except Exception as e:
            print(f"[LỖI MẠNG] {e}")
            time.sleep(5)

@app.route('/api/start', methods=['POST'])
def start():
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Sai API Key!"}), 401
    
    data = request.json
    token = data.get('token')
    channel = data.get('channel')
    message = data.get('message')
    delay = float(data.get('delay', 3))

    if not token or not channel or not message:
        return jsonify({"error": "Thiếu thông tin!"}), 400

    # Chạy ngầm vòng lặp vô tận
    threading.Thread(target=send_spam, args=(token, channel, message, delay), daemon=True).start()
    
    return jsonify({"status": "success", "message": "Đã bắt đầu!"})

# Trang chủ hiển thị HTML nếu bạn up chung file index.html lên GitHub
@app.route('/')
def index():
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return "API đang chạy trên Render!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
