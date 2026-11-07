import sqlite3
import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --------------------------------------------------------------------------
# TẦNG DỮ LIỆU (DATABASE LAYER) - QUẢN LÝ LỊCH SỬ GIAO THÔNG VỚI SQLITE
# --------------------------------------------------------------------------

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "traffic_history.db")

def init_db():
    """Khởi tạo cấu trúc bảng nếu chưa tồn tại"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            n1 INTEGER,
            n2 INTEGER,
            green1 INTEGER,
            green2 INTEGER,
            yellow INTEGER,
            mode TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_traffic(n1, n2, green1, green2, yellow=3, mode="AUTO"):
    """Ghi nhận log mật độ xe và chu kỳ đèn vào Database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO traffic_logs (timestamp, n1, n2, green1, green2, yellow, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (current_time, n1, n2, green1, green2, yellow, mode))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Không thể lưu log: {e}")

def get_recent_logs(limit=20):
    """Lấy N bản ghi gần nhất để hiển thị bảng lịch sử và biểu đồ"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, n1, n2, green1, green2, mode
            FROM traffic_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        logs = []
        for r in reversed(rows):  # Đảo ngược để biểu đồ chạy từ quá khứ đến hiện tại
            logs.append({
                "id": r[0],
                "time": r[1].split(" ")[1] if " " in r[1] else r[1],  # Lấy HH:MM:SS
                "full_time": r[1],
                "n1": r[2],
                "n2": r[3],
                "green1": r[4],
                "green2": r[5],
                "mode": r[6]
            })
        return logs
    except Exception as e:
        print(f"[DB ERROR] Lỗi truy vấn: {e}")
        return []

def get_stats():
    """Thống kê tổng quan: Tổng lượt đo, mật độ xe trung bình"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), AVG(n1), AVG(n2), MAX(n1), MAX(n2) FROM traffic_logs")
        row = cursor.fetchone()
        conn.close()
        return {
            "total_records": row[0] or 0,
            "avg_n1": round(row[1] or 0, 1),
            "avg_n2": round(row[2] or 0, 1),
            "max_n1": row[3] or 0,
            "max_n2": row[4] or 0
        }
    except Exception:
        return {"total_records": 0, "avg_n1": 0, "avg_n2": 0, "max_n1": 0, "max_n2": 0}

# Tự động khởi tạo DB khi nạp module
init_db()
