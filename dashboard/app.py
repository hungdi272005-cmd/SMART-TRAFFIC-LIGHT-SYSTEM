import json
import os
import sys

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi UnicodeEncodeError (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request

# Thêm thư mục gốc vào path để import database
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database import db_manager as db

# --------------------------------------------------------------------------
# TẦNG ỨNG DỤNG (APPLICATION LAYER) - WEB DASHBOARD GIÁM SÁT GIAO THÔNG
# --------------------------------------------------------------------------

app = Flask(__name__)

# Trạng thái hệ thống thời gian thực
traffic_data = {
    "n1": 0,
    "n2": 0,
    "green1": 15,
    "green2": 15,
    "yellow": 3,
    "mode": "ADAPTIVE_AI",
    "mqtt_connected": False,
}

# MQTT Client
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        traffic_data["mqtt_connected"] = True
        print("[DASHBOARD MQTT] Đã kết nối Broker!")
        client.subscribe("traffic/sa_ban/timing")
    else:
        traffic_data["mqtt_connected"] = False

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        traffic_data["n1"] = payload.get("n1", traffic_data["n1"])
        traffic_data["n2"] = payload.get("n2", traffic_data["n2"])
        traffic_data["green1"] = payload.get("green1", traffic_data["green1"])
        traffic_data["green2"] = payload.get("green2", traffic_data["green2"])

        # TỰ ĐỘNG LƯU LOG VÀO DATABASE SQLITE
        db.log_traffic(
            n1=traffic_data["n1"],
            n2=traffic_data["n2"],
            green1=traffic_data["green1"],
            green2=traffic_data["green2"],
            yellow=traffic_data["yellow"],
            mode=traffic_data["mode"]
        )
    except Exception as e:
        print(f"Lỗi đọc MQTT: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect("localhost", 1883, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"[DASHBOARD] Chưa kết nối được MQTT Broker: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def status():
    return jsonify(traffic_data)

@app.route("/api/history")
def history():
    """API trả về dữ liệu lịch sử để vẽ biểu đồ và bảng thống kê"""
    logs = db.get_recent_logs(limit=25)
    stats = db.get_stats()
    return jsonify({"history": logs, "stats": stats})

@app.route("/api/control", methods=["POST"])
def control():
    body = request.get_json() or {}
    mode = body.get("mode", "AUTO")
    traffic_data["mode"] = mode

    # Ghi đè chế độ ưu tiên
    if mode == "EMERGENCY_P1":
        traffic_data["green1"] = 40
        traffic_data["green2"] = 10
    elif mode == "EMERGENCY_P2":
        traffic_data["green1"] = 10
        traffic_data["green2"] = 40

    mqtt_client.publish(
        "traffic/sa_ban/timing",
        json.dumps({
            "green1": traffic_data["green1"],
            "green2": traffic_data["green2"],
            "yellow": 3,
            "n1": traffic_data["n1"],
            "n2": traffic_data["n2"],
        }),
    )

    # Lưu log sự kiện can thiệp khẩn cấp vào DB
    db.log_traffic(
        n1=traffic_data["n1"],
        n2=traffic_data["n2"],
        green1=traffic_data["green1"],
        green2=traffic_data["green2"],
        yellow=3,
        mode=mode
    )
    return jsonify({"status": "success", "mode": mode})

if __name__ == "__main__":
    print("\n" + "="*50)
    print(">> WEB DASHBOARD & DATABASE ĐANG CHẠY TẠI: http://localhost:5000")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
