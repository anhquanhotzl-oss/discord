from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import requests
import time
import os
import uuid

app = Flask(__name__, static_folder='.')
CORS(app)

API_KEY = "ADMIN2026"
# Lưu trữ trạng thái các task: True = Đang chạy, False = Tạm dừng
task_states = {} 

def send_spam(task_id, token, channel_id, content, delay):
    count = 0
    while task_id in task_states: # Nếu task vẫn tồn tại trong danh sách
        if task_states[task_id] == False: # Nếu đang bị tạm dừng
            time.sleep(2) # Chờ 2 giây rồi kiểm tra lại
            continue
            
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
                print(f"[LỖI] Token của task {task_id} chết.")
                if task_id in task_states: del task_states[task_id]
                break
            
            if res.status_code == 200:
                count += 1
                print(f"[OK] Task {task_id} - Đã gửi {count} tin nhắn.")
                
            time.sleep(delay)
        except Exception as e:
            time.sleep(5)

# API 1: Bắt đầu Task
@app.route('/api/start', methods=['POST'])
def start():
    if request.headers.get('X-API-KEY') != API_KEY: return jsonify({"error": "Sai Key"}), 401
    data = request.json
    
    task_id = str(uuid.uuid4())[:8]
    task_states[task_id] = True # True = Đang chạy
    
    threading.Thread(target=send_spam, args=(task_id, data['token'], data['channel'], data['message'], float(data['delay'])), daemon=True).start()
    
    return jsonify({"status": "success", "task_id": task_id})

# API 2: Tạm dừng / Chạy tiếp
@app.route('/api/toggle', methods=['POST'])
def toggle():
    if request.headers.get('X-API-KEY') != API_KEY: return jsonify({"error": "Sai Key"}), 401
    task_id = request.json.get('task_id')
    
    if task_id in task_states:
        task_states[task_id] = not task_states[task_id] # Đảo ngược trạng thái
        return jsonify({"status": "success", "is_running": task_states[task_id]})
    return jsonify({"error": "Không tìm thấy task"}), 404

# API 3: Xóa Task
@app.route('/api/delete', methods=['POST'])
def delete():
    if request.headers.get('X-API-KEY') != API_KEY: return jsonify({"error": "Sai Key"}), 401
    task_id = request.json.get('task_id')
    
    if task_id in task_states:
        del task_states[task_id] # Xóa khỏi danh sách -> vòng lặp tự dừng
        return jsonify({"status": "success"})
    return jsonify({"error": "Không tìm thấy task"}), 404

@app.route('/')
def index():
    if os.path.exists('index.html'): return send_from_directory('.', 'index.html')
    return "API đang chạy!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
