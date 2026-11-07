import cv2
import json
import os
import sys
import time
from collections import deque
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import paho.mqtt.client as mqtt
from ultralytics import YOLO

# --------------------------------------------------------------------------
# HỆ THỐNG AI ĐIỀU KHIỂN ĐÈN GIAO THÔNG THÍCH ỨNG THỜI GIAN THỰC (NHÓM 11)
# --------------------------------------------------------------------------
# Hỗ trợ cả 2 chế độ:
# 1. Camera thật: Đọc luồng DroidCam iPhone / Webcam
# 2. Giả lập ảnh: Dùng ảnh sa bàn mẫu để test trước khi lắp xong phần cứng
# --------------------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "configs", "config.json")
ROI_PATH = os.path.join(PROJECT_ROOT, "configs", "roi_points.json")

# 1. Đọc cấu hình
config = {
    "camera": {"source": "assets/demo_saban.jpg"},
    "mqtt": {"broker": "localhost", "port": 1883, "topic_timing": "traffic/sa_ban/timing"},
    "traffic_timing": {"t_min": 10, "t_max": 35, "t_yellow": 3, "t_default": 15},
    "ai": {"confidence_threshold": 0.25, "moving_average_frames": 30}
}

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            print("[INFO] Đã nạp cấu hình từ configs/config.json")
    except Exception as e:
        print(f"[WARN] Lỗi đọc config: {e}")

# 2. Kiểm tra tọa độ ROI
if not os.path.exists(ROI_PATH):
    print("\n[LỖI CHÍ MẠNG] Chưa có file tọa độ configs/roi_points.json!")
    print(">> Vui lòng chạy trước: python ai_service/roi_selector.py để khoanh 2 vùng làn xe.\n")
    exit()

with open(ROI_PATH, "r", encoding="utf-8") as f:
    roi_data = json.load(f)

pts_roi1 = np.array(roi_data["roi_lane1"], np.int32).reshape((-1, 1, 2))
pts_roi2 = np.array(roi_data["roi_lane2"], np.int32).reshape((-1, 1, 2))

# 3. Khởi tạo MQTT Client
mqtt_client = mqtt.Client()
mqtt_connected = False

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print("[MQTT] Đã kết nối Broker!")
    else:
        print(f"[MQTT] Kết nối thất bại: {rc}")

mqtt_client.on_connect = on_connect

broker_addr = config.get("mqtt", {}).get("broker", "localhost")
broker_port = config.get("mqtt", {}).get("port", 1883)
topic_timing = config.get("mqtt", {}).get("topic_timing", "traffic/sa_ban/timing")

try:
    mqtt_client.connect(broker_addr, broker_port, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"[MQTT WARN] Không thể kết nối Broker: {e} (vẫn chạy AI bình thường)")

# 4. Tải mô hình YOLOv8n
print("[INFO] Đang nạp mô hình YOLOv8n...")
model = YOLO("yolov8n.pt")

# 5. Khởi tạo Nguồn Video / Ảnh mẫu
video_src = config.get("camera", {}).get("source", "assets/demo_saban.jpg")
is_image = False
sample_img = None

if isinstance(video_src, str) and (video_src.endswith(".jpg") or video_src.endswith(".png") or video_src.endswith(".jpeg")):
    img_path = video_src if os.path.isabs(video_src) else os.path.join(PROJECT_ROOT, video_src)
    if os.path.exists(img_path):
        sample_img = cv2.imread(img_path)
        is_image = True
        print(f">> [CHẾ ĐỘ GIẢ LẬP] Đang chạy với ảnh sa bàn: {img_path}")

if not is_image:
    try:
        source_idx = int(video_src)
    except (ValueError, TypeError):
        source_idx = video_src
    cap = cv2.VideoCapture(source_idx)
    if not cap.isOpened():
        print(f"[CANH BAO] Không mở được Camera {video_src}, tự động chuyển sang ảnh mẫu.")
        sample_img = cv2.imread(os.path.join(PROJECT_ROOT, "assets", "demo_saban.jpg"))
        is_image = True

# Bộ đệm Moving Average
ma_window = config.get("ai", {}).get("moving_average_frames", 30)
lane1_history = deque(maxlen=ma_window)
lane2_history = deque(maxlen=ma_window)

t_min = config.get("traffic_timing", {}).get("t_min", 10)
t_max = config.get("traffic_timing", {}).get("t_max", 35)
t_yellow = config.get("traffic_timing", {}).get("t_yellow", 3)
t_default = config.get("traffic_timing", {}).get("t_default", 15)
# Hạ ngưỡng tin cậy xuống 0.08 để bắt nhạy toàn bộ xe đồ chơi nhỏ/khuất
conf_thresh = 0.08

# Các lớp ngoại trừ (người/bàn tay, trụ đèn, vật dụng lớn ngoài sa bàn)
EXCLUDED_CLASSES = {0, 9, 59, 60, 62, 63, 76}

cv2.namedWindow("SMART TRAFFIC SYSTEM - AI CONTROLLER", cv2.WINDOW_NORMAL)
cv2.resizeWindow("SMART TRAFFIC SYSTEM - AI CONTROLLER", 1100, 620)

last_mqtt_send_time = 0
SEND_INTERVAL_SEC = 2.0

print("\n" + "="*50)
print(">> AI CONTROLLER ĐANG CHẠY...")
print(">> Nhấn phím 'q' trên cửa sổ hình ảnh để dừng.")
print("="*50 + "\n")

while True:
    if is_image:
        frame = sample_img.copy()
        time.sleep(0.03)  # Giả lập ~30 FPS
    else:
        ret, frame = cap.read()
        if not ret:
            break

    # Chạy YOLOv8 với imgsz=1280 và agnostic_nms=True để hợp nhất các hộp nhận diện trùng lặp
    results = model(frame, imgsz=1280, conf=conf_thresh, agnostic_nms=True, verbose=False)

    raw_count_1 = 0
    raw_count_2 = 0
    display_frame = frame.copy()

    # Phủ màu 2 vùng ROI
    overlay = display_frame.copy()
    cv2.fillPoly(overlay, [pts_roi1], (0, 140, 255))
    cv2.fillPoly(overlay, [pts_roi2], (255, 180, 0))
    cv2.addWeighted(overlay, 0.25, display_frame, 0.75, 0, display_frame)

    cv2.polylines(display_frame, [pts_roi1], True, (0, 140, 255), 2)
    cv2.polylines(display_frame, [pts_roi2], True, (255, 180, 0), 2)

    # Đếm xe theo từng ROI
    boxes = results[0].boxes
    for box in boxes:
        cls_id = int(box.cls[0])
        if cls_id in EXCLUDED_CLASSES:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        box_w = x2 - x1
        box_h = y2 - y1
        area = box_w * box_h

        # Lọc theo kích thước thực tế của xe đồ chơi tỷ lệ 1:64 trên khung hình 1280x720
        # Loại bỏ các vết nhiễu quá nhỏ (< 300 px) hoặc vật thể quá to (> 25000 px)
        if area < 300 or area > 25000:
            continue

        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        base_y = int(y2 - 5)  # Điểm tiếp đất chân bánh xe

        in_roi1 = (cv2.pointPolygonTest(pts_roi1, (cx, cy), False) >= 0 or 
                   cv2.pointPolygonTest(pts_roi1, (cx, base_y), False) >= 0)
        in_roi2 = (cv2.pointPolygonTest(pts_roi2, (cx, cy), False) >= 0 or 
                   cv2.pointPolygonTest(pts_roi2, (cx, base_y), False) >= 0)

        conf = float(box.conf[0])
        if in_roi1:
            raw_count_1 += 1
            color = (0, 140, 255)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(display_frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(display_frame, f"Xe {int(conf*100)}%", (x1, max(15, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        elif in_roi2:
            raw_count_2 += 1
            color = (255, 180, 0)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(display_frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(display_frame, f"Xe {int(conf*100)}%", (x1, max(15, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    # Moving Average
    lane1_history.append(raw_count_1)
    lane2_history.append(raw_count_2)
    n1 = int(round(np.mean(lane1_history)))
    n2 = int(round(np.mean(lane2_history)))

    # Thuật toán tính T_green
    total_vehicles = n1 + n2
    if total_vehicles == 0:
        t_green1 = t_default
        t_green2 = t_default
    else:
        t_extra = t_max - t_min
        t_green1 = int(round(np.clip(t_min + (n1 / total_vehicles) * t_extra, t_min, t_max)))
        t_green2 = int(round(np.clip(t_min + (n2 / total_vehicles) * t_extra, t_min, t_max)))

    # Gửi MQTT định kỳ
    current_time = time.time()
    if current_time - last_mqtt_send_time >= SEND_INTERVAL_SEC:
        payload = {
            "green1": t_green1,
            "green2": t_green2,
            "yellow": t_yellow,
            "n1": n1,
            "n2": n2
        }
        if mqtt_connected:
            mqtt_client.publish(topic_timing, json.dumps(payload))
        last_mqtt_send_time = current_time

    # Bảng HUD hiển thị
    hud_h, hud_w = 175, 420
    hud = np.zeros((hud_h, hud_w, 3), dtype=np.uint8)
    hud[:] = (30, 30, 30)

    cv2.putText(hud, "SMART TRAFFIC - NHOM 11", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
    mqtt_str = "MQTT: ONLINE" if mqtt_connected else "MQTT: OFFLINE"
    mqtt_col = (0, 255, 0) if mqtt_connected else (0, 0, 255)
    cv2.putText(hud, mqtt_str, (280, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, mqtt_col, 1)

    cv2.line(hud, (15, 35), (hud_w - 15, 35), (100, 100, 100), 1)

    cv2.putText(hud, f"[TRUC 1: BAC - NAM]", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)
    cv2.putText(hud, f"So xe N1: {n1} xe", (15, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(hud, f"TG Xanh: {t_green1} giay", (15, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

    cv2.putText(hud, f"[TRUC 2: DONG - TAY]", (220, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 180, 0), 1)
    cv2.putText(hud, f"So xe N2: {n2} xe", (220, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(hud, f"TG Xanh: {t_green2} giay", (220, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

    cv2.line(hud, (15, 125), (hud_w - 15, 125), (100, 100, 100), 1)
    mode_text = "[GIA LAP ANH MAU]" if is_image else "[CAMERA LIVE]"
    cv2.putText(hud, f"Che do: {mode_text} | Vang: {t_yellow}s", (15, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    cv2.putText(hud, f"JSON: {{\"green1\": {t_green1}, \"green2\": {t_green2}}}", (15, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 220, 150), 1)

    display_frame[10:10+hud_h, 10:10+hud_w] = hud

    cv2.imshow("SMART TRAFFIC SYSTEM - AI CONTROLLER", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if not is_image:
    cap.release()
cv2.destroyAllWindows()
if mqtt_connected:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
print(">> Đã đóng hệ thống an toàn.")
