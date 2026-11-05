from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import requests
import time
import os
import uuid

app = Flask(__name__)
CORS(app)

API_KEY = "ADMIN2026"
running_tasks = {}

def send_spam(task_id, token, channel_id, content, delay):
    while task_id in running_tasks:
        if running_tasks[task_id] == False: # Trạng thái tạm dừng
            time.sleep(2)
            continue
        try:
            headers = {"Authorization": token, "Content-Type": "application/json"}
            res = requests.post(
                f"https://discord.com/api/v9/channels/{channel_id}/messages",
                headers=headers, json={"content": content}
            )
            if res.status_code == 429:
                time.sleep(5)
                continue
            if res.status_code in [401, 403]:
                if task_id in running_tasks: del running_tasks[task_id]
                break
            time.sleep(delay)
        except Exception:
            time.sleep(5)

@app.route('/api/start', methods=['POST'])
def start():
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Sai API Key!"}), 401
    data = request.json
    task_id = str(uuid.uuid4())[:8]
    running_tasks[task_id] = True
    threading.Thread(target=send_spam, args=(task_id, data['token'], data['channel'], data['message'], float(data['delay'])), daemon=True).start()
    return jsonify({"status": "success", "task_id": task_id})

@app.route('/api/toggle', methods=['POST'])
def toggle():
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Sai API Key!"}), 401
    task_id = request.json.get('task_id')
    if task_id in running_tasks:
        running_tasks[task_id] = not running_tasks[task_id]
        return jsonify({"status": "success", "is_running": running_tasks[task_id]})
    return jsonify({"error": "Không tìm thấy task!"}), 404

@app.route('/api/delete', methods=['POST'])
def delete():
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Sai API Key!"}), 401
    task_id = request.json.get('task_id')
    if task_id in running_tasks:
        del running_tasks[task_id]
        return jsonify({"status": "success"})
    return jsonify({"error": "Không tìm thấy task!"}), 404

# Route mặc định để kiểm tra server sống hay chết
@app.route('/')
def home():
    return "API Tool Treo Discord đang chạy!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
