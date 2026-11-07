# HƯỚNG DẪN ĐẤU DÂY VÀ BỐ TRÍ SA BÀN - NHÓM 11

## 1. Nguyên lý phân pha và cắm chân GPIO trên ESP32

Mỗi module đèn giao thông có 4 chân:
- `GND`: Cực âm chung
- `R`: Đèn Đỏ (Red)
- `Y`: Đèn Vàng (Yellow)
- `G`: Đèn Xanh (Green)

### Bảng kết nối chân GPIO đề xuất:

| Tín hiệu | Module Đèn | Chân trên Module | Chân GPIO ESP32 | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **GND chung** | Tất cả các đèn | `GND` | `GND` trên ESP32 | Cắm vào đường bus âm trên Breadboard |
| **PHA 1: TRỤC DỌC (Bắc - Nam)** | **Đèn 1 & Đèn 2** (Đấu song song) | `R` (Đỏ 1) | **GPIO 25** | Chụm 2 chân R vào cùng 1 hàng Breadboard |
| | | `Y` (Vàng 1) | **GPIO 26** | Chụm 2 chân Y vào cùng 1 hàng Breadboard |
| | | `G` (Xanh 1) | **GPIO 27** | Chụm 2 chân G vào cùng 1 hàng Breadboard |
| **PHA 2: TRỤC NGANG (Đông - Tây)** | **Đèn 3** | `R` (Đỏ 2) | **GPIO 14** | |
| | | `Y` (Vàng 2) | **GPIO 12** | |
| | | `G` (Xanh 2) | **GPIO 13** | |

---

## 2. Sơ đồ mạch trực quan (Breadboard Wiring)

```text
       ESP32 NodeMCU
    +-----------------+
    | GND         GND |-----> ĐƯỜNG CỰC ÂM (-) TRÊN BREADBOARD ---> GND cả 3 đèn
    | ...             |
    | GPIO 25 (P1_R)  |-----------------------------> R của Đèn 1 & Đèn 2 (chụm lại)
    | GPIO 26 (P1_Y)  |-----------------------------> Y của Đèn 1 & Đèn 2 (chụm lại)
    | GPIO 27 (P1_G)  |-----------------------------> G của Đèn 1 & Đèn 2 (chụm lại)
    |                 |
    | GPIO 14 (P2_R)  |-----------------------------> R của Đèn 3
    | GPIO 12 (P2_Y)  |-----------------------------> Y của Đèn 3
    | GPIO 13 (P2_G)  |-----------------------------> G của Đèn 3
    +-----------------+
```
