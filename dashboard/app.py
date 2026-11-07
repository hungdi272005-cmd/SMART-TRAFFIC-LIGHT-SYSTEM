import json
import os
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request

# --------------------------------------------------------------------------
# TẦNG ỨNG DỤNG (APPLICATION LAYER) - WEB DASHBOARD GIÁM SÁT GIAO THÔNG
# --------------------------------------------------------------------------

app = Flask(__name__)

# Trạng thái hệ thống thời gian thực
traffic_data = {
    "n1": 2,
    "n2": 4,
    "green1": 18,
    "green2": 27,
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


@app.route("/api/control", methods=["POST"])
def control():
    body = request.get_json() or {}
    mode = body.get("mode", "AUTO")
    traffic_data["mode"] = mode

    # Gửi lệnh ghi đè qua MQTT
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
    return jsonify({"status": "success", "mode": mode})


if __name__ == "__main__":
    print("[INFO] Web Dashboard đang khởi chạy tại: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
