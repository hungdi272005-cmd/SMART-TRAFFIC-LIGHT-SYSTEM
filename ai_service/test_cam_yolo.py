import cv2
import json
import os
from ultralytics import YOLO

# Đọc cấu hình từ file configs/config.json nếu có
config_path = os.path.join(os.path.dirname(__file__), "..", "configs", "config.json")
video_source = 0

if os.path.exists(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            video_source = cfg.get("camera", {}).get("source", 0)
    except Exception as e:
        print(f"Không thể đọc config, dùng mặc định: {e}")

print("Đang nạp mô hình YOLOv8n...")
model = YOLO("yolov8n.pt")

print(f"Đang kết nối camera: {video_source}")
cap = cv2.VideoCapture(video_source)

if not cap.isOpened():
    print(f"\n[LỖI] Không thể mở Camera nguồn {video_source}!")
    print("Mẹo: Mở file configs/config.json để kiểm tra lại nguồn camera (0, 1 hoặc IP Wi-Fi).")
    exit()

print(">> Đã kết nối Camera thành công. Nhấn 'q' để thoát.")
VEHICLE_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck

while True:
    ret, frame = cap.read()
    if not ret:
        print("Mất tín hiệu camera...")
        break

    results = model(frame, conf=0.25, classes=VEHICLE_CLASSES, verbose=False)
    car_count = len(results[0].boxes)

    annotated = results[0].plot()
    cv2.putText(
        annotated,
        f"Phat hien: {car_count} phuong tien",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )

    cv2.imshow("TEST DROIDCAM & YOLOV8 - NHOM 11", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
