from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import requests
import time
import uuid
import datetime

app = Flask(__name__)
CORS(app)

# ================= CƠ SỞ DỮ LIỆU (LƯU TRONG RAM) =================
ADMIN_USER = "ngduclam"
ADMIN_PASS = "ndl1201"

USERS_DB = {
    ADMIN_USER: {"password": ADMIN_PASS, "role": "admin"}
}

def send_spam(username, task_id, token, channel_id, content, delay):
    while task_id in USERS_DB.get(username, {}).get("tasks", {}):
        if USERS_DB[username]["tasks"][task_id] == False:
            time.sleep(2); continue
        try:
            headers = {"Authorization": token, "Content-Type": "application/json"}
            res = requests.post(f"https://discord.com/api/v9/channels/{channel_id}/messages", headers=headers, json={"content": content})
            if res.status_code == 429:
                time.sleep(5); continue
            if res.status_code in [401, 403]:
                if task_id in USERS_DB[username]["tasks"]: del USERS_DB[username]["tasks"][task_id]
                break
            time.sleep(delay)
        except:
            time.sleep(5)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    device_id = data.get('device_id')

    if username not in USERS_DB:
        return jsonify({"error": "Tài khoản không tồn tại!"}), 401
    
    user = USERS_DB[username]
    if user["password"] != password:
        return jsonify({"error": "Sai mật khẩu!"}), 401

    if username == ADMIN_USER:
        return jsonify({"status": "success", "role": "admin", "username": username})

    # Kiểm tra hạn
    expire_date = datetime.datetime.strptime(user["expire_date"], "%Y-%m-%d")
    if datetime.datetime.now() > expire_date:
        return jsonify({"error": "Tài khoản đã hết hạn!"}), 403

    # Kiểm tra thiết bị
    if user["device_id"] is None:
        user["device_id"] = device_id # Gắn thiết bị
    elif user["device_id"] != device_id:
        return jsonify({"error": "Tài khoản đã bị khóa trên thiết bị khác!"}), 403

    return jsonify({"status": "success", "role": "user", "username": username})

@app.route('/api/start', methods=['POST'])
def start():
    data = request.json
    username = data.get('username')
    if username not in USERS_DB: return jsonify({"error": "Lỗi xác thực!"}), 401
    
    task_id = str(uuid.uuid4())[:8]
    if "tasks" not in USERS_DB[username]: USERS_DB[username]["tasks"] = {}
    
    USERS_DB[username]["tasks"][task_id] = True
    threading.Thread(target=send_spam, args=(username, task_id, data['token'], data['channel'], data['message'], float(data['delay'])), daemon=True).start()
    return jsonify({"status": "success", "task_id": task_id})

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    res = []
    for u, data in USERS_DB.items():
        if u == ADMIN_USER: continue
        res.append({"username": u, "device_id": data.get("device_id"), "expire_date": data.get("expire_date")})
    return jsonify({"users": res})

@app.route('/api/admin/create', methods=['POST'])
def create_user():
    data = request.json
    u, p, days = data.get('username'), data.get('password'), int(data.get('days', 30))
    if u in USERS_DB: return jsonify({"error": "Tài khoản đã tồn tại!"}), 400
    expire = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    USERS_DB[u] = {"password": p, "device_id": None, "expire_date": expire, "tasks": {}}
    return jsonify({"status": "success"})

@app.route('/api/admin/reset_device', methods=['POST'])
def reset_device():
    u = request.json.get('username')
    if u in USERS_DB:
        USERS_DB[u]["device_id"] = None
        return jsonify({"status": "success"})
    return jsonify({"error": "Lỗi"}), 404

@app.route('/api/admin/delete', methods=['POST'])
def delete_user():
    u = request.json.get('username')
    if u in USERS_DB and u != ADMIN_USER:
        del USERS_DB[u]
        return jsonify({"status": "success"})
    return jsonify({"error": "Lỗi"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
