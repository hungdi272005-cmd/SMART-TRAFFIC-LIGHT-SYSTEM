import cv2
import json
import os
import numpy as np

# --------------------------------------------------------------------------
# CÔNG CỤ CHỌN VÙNG QUAN SÁT (ROI SELECTOR) CHO SA BÀN GIAO THÔNG
# --------------------------------------------------------------------------
# Hỗ trợ cả 2 chế độ:
# 1. Camera thật: DroidCam / Webcam USB / IP Camera.
# 2. Ảnh giả lập: Dùng ảnh mẫu khi chưa lắp xong phần cứng (Test AI trước).
# --------------------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "configs", "config.json")
ROI_SAVE_PATH = os.path.join(PROJECT_ROOT, "configs", "roi_points.json")

# Đọc cấu hình nguồn video/ảnh
video_source = "assets/demo_saban.jpg"
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            video_source = cfg.get("camera", {}).get("source", "assets/demo_saban.jpg")
    except Exception as e:
        print(f"Lỗi đọc config: {e}")

# Kiểm tra xem video_source là ảnh mẫu hay Camera
is_image = False
sample_img = None

if isinstance(video_source, str) and (video_source.endswith(".jpg") or video_source.endswith(".png") or video_source.endswith(".jpeg")):
    img_path = video_source if os.path.isabs(video_source) else os.path.join(PROJECT_ROOT, video_source)
    if os.path.exists(img_path):
        sample_img = cv2.imread(img_path)
        is_image = True
        print(f">> [CHE DO GIA LAP] Dang dung anh sa ban mau: {img_path}")
    else:
        print(f"[CANH BAO] Khong tim thay anh {img_path}, thu mo Camera...")

if not is_image:
    try:
        source_idx = int(video_source)
    except (ValueError, TypeError):
        source_idx = video_source
    cap = cv2.VideoCapture(source_idx)
    if not cap.isOpened():
        print(f"[CANH BAO] Khong mo duoc Camera {video_source}! Tu dong chuyen sang anh mau.")
        img_path = os.path.join(PROJECT_ROOT, "assets", "demo_saban.jpg")
        sample_img = cv2.imread(img_path)
        is_image = True

current_points = []
all_rois = {"roi_lane1": [], "roi_lane2": []}
current_lane = 1

def mouse_callback(event, x, y, flags, param):
    global current_points, all_rois, current_lane
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(current_points) < 4:
            current_points.append([x, y])
            print(f"-> ROI {current_lane} - Diem {len(current_points)}: ({x}, {y})")

        if len(current_points) == 4:
            if current_lane == 1:
                all_rois["roi_lane1"] = list(current_points)
                current_points = []
                current_lane = 2
                print(">> DA XONG ROI 1 (Truc Bac - Nam)! Hay click 4 diem cho ROI 2 (Truc Dong - Tay).")
            elif current_lane == 2:
                all_rois["roi_lane2"] = list(current_points)
                current_points = []
                current_lane = 3
                print(">> DA CHON DU 2 VUNG! Nhan 's' de LUU toa do, hoac 'r' de CHON LAI.")

cv2.namedWindow("ROI SELECTOR - NHOM 11", cv2.WINDOW_NORMAL)
cv2.resizeWindow("ROI SELECTOR - NHOM 11", 1100, 620)
cv2.setMouseCallback("ROI SELECTOR - NHOM 11", mouse_callback)

print("\n=== HUONG DAN CHON ROI ===")
print("1. Click 4 diem de khoanh vung cho TRUC 1 (Bac - Nam: vung co xe cho)")
print("2. Click tiep 4 diem de khoanh vung cho TRUC 2 (Dong - Tay: vung co xe cho)")
print("3. Nhan 's' de LUU, 'r' de RESET, 'q' de THOAT.\n")

while True:
    if is_image:
        frame = sample_img.copy()
    else:
        ret, frame = cap.read()
        if not ret:
            print("Mat tin hieu camera...")
            break

    display_frame = frame.copy()

    # Vẽ ROI 1 (Màu Cam)
    if len(all_rois["roi_lane1"]) == 4:
        pts1 = np.array(all_rois["roi_lane1"], np.int32).reshape((-1, 1, 2))
        cv2.polylines(display_frame, [pts1], isClosed=True, color=(0, 140, 255), thickness=2)
        cv2.putText(display_frame, "ROI 1: BAC - NAM", (all_rois["roi_lane1"][0][0], all_rois["roi_lane1"][0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)

    # Vẽ ROI 2 (Màu Vàng / Xanh dương)
    if len(all_rois["roi_lane2"]) == 4:
        pts2 = np.array(all_rois["roi_lane2"], np.int32).reshape((-1, 1, 2))
        cv2.polylines(display_frame, [pts2], isClosed=True, color=(255, 180, 0), thickness=2)
        cv2.putText(display_frame, "ROI 2: DONG - TAY", (all_rois["roi_lane2"][0][0], all_rois["roi_lane2"][0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 180, 0), 2)

    # Vẽ các điểm đang click
    for pt in current_points:
        cv2.circle(display_frame, tuple(pt), 5, (0, 255, 0), -1)
    if len(current_points) > 1:
        cv2.polylines(display_frame, [np.array(current_points, np.int32).reshape((-1, 1, 2))], isClosed=False, color=(0, 255, 0), thickness=1)

    # Hiển thị thanh trạng thái
    if current_lane == 1:
        tip = f"Dang chon ROI 1 (Bac - Nam): {len(current_points)}/4 diem"
        color = (0, 140, 255)
    elif current_lane == 2:
        tip = f"Dang chon ROI 2 (Dong - Tay): {len(current_points)}/4 diem"
        color = (255, 180, 0)
    else:
        tip = "DA CHON DU 2 VUNG! Nhan 's' de LUU, 'r' de RESET"
        color = (0, 255, 0)

    # Hộp thông tin trên cùng
    cv2.rectangle(display_frame, (10, 10), (620, 50), (30, 30, 30), -1)
    cv2.putText(display_frame, tip, (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("ROI SELECTOR - NHOM 11", display_frame)

    key = cv2.waitKey(30) & 0xFF
    if key == ord('s'):
        if len(all_rois["roi_lane1"]) == 4 and len(all_rois["roi_lane2"]) == 4:
            with open(ROI_SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(all_rois, f, indent=2)
            print(f"\n[THANH CONG] Toa do da duoc luu tai: {ROI_SAVE_PATH}")
            break
        else:
            print("[CANH BAO] Ban chua chon du 4 diem cho ca 2 vung ROI!")
    elif key == ord('r'):
        current_points = []
        all_rois = {"roi_lane1": [], "roi_lane2": []}
        current_lane = 1
        print(">> DA RESET. Vui long chon lai tu dau.")
    elif key == ord('q'):
        break

if not is_image:
    cap.release()
cv2.destroyAllWindows()
