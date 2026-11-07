# SMART TRAFFIC LIGHT SYSTEM (HỆ THỐNG ĐÈN GIAO THÔNG THÍCH ỨNG DÙNG AI & IOT)

**Nhóm 11 - Đề tài nghiên cứu ứng dụng**
* Nguyễn Ngọc Sơn (20235415)
* Tô Huy Thông (20235435)
* Nguyễn Đức Bảo Minh (20235378)
* Nguyễn Mạnh Hùng (20235339)

---

## 📁 Cấu trúc thư mục dự án

```text
SMART-TRAFFIC-LIGHT-SYSTEM/
│
├── ai_service/                 # Tầng Middleware / AI Engine
│   ├── test_cam_yolo.py        # Script test nhanh camera & phát hiện xe đồ chơi
│   ├── roi_selector.py         # Công cụ vẽ & lưu tọa độ 2 vùng ROI (Bắc-Nam & Đông-Tây)
│   ├── traffic_optimizer.py    # Thuật toán co giãn thời gian xanh theo mật độ N1, N2
│   └── main_ai_traffic.py      # Script chính chạy luồng khép kín (Camera -> YOLO -> MQTT)
│
├── firmware_esp32/             # Tầng Sensing & Actuation (Lập trình ESP32)
│   └── traffic_light_fsm/
│       └── traffic_light_fsm.ino # Code Arduino IDE (FSM 4 pha, Double Buffering, Failsafe)
│
├── dashboard/                  # Tầng Application Layer (Giao diện Web giám sát)
│   └── app.py                  # Web Dashboard giám sát video stream & nút ghi đè
│
├── configs/                    # Thư mục cấu hình tập trung
│   ├── config.json             # Cấu hình IP camera, MQTT Broker, T_min, T_max...
│   └── roi_points.json         # Tọa độ vùng nhận diện (được tạo tự động từ roi_selector)
│
├── docs/                       # Báo cáo, sơ đồ đấu nối phần cứng, slide bảo vệ
│
├── requirements.txt            # Thư viện Python cần cài
├── .gitignore
└── README.md
```

---

## 🚀 Hướng dẫn bắt đầu nhanh

### 1. Cài đặt thư viện Python
```bash
pip install -r requirements.txt
```

### 2. Cấu hình Camera & MQTT
Mở file `configs/config.json` để chỉnh sửa nguồn camera (`0`, `1` hoặc link Wi-Fi `http://...`) và địa chỉ Mosquitto MQTT Broker.
