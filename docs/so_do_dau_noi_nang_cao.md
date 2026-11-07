# SƠ ĐỒ ĐẤU DÂY CHUẨN XÁC NHẤT (ESP32 DEVKIT V1 + 4 CỤM ĐÈN XE + OLED SPI)

*(Phiên bản đã tối ưu: Không cần chân D15, bỏ 2 LED đi bộ, 100% chân cắm đều có in chữ rõ ràng trên bo)*

---

## 1. Màn hình OLED SPI 0.96 inch (7 chân)

| Chân trên OLED | Chân trên ESP32 DevKit V1 | Vị trí trên Bo mạch |
| :--- | :--- | :--- |
| **GND** | **GND** | Hàng chân âm (-) Breadboard |
| **VCC** | **3V3** (hoặc VIN nếu màn hỗ trợ 5V) | Cấp nguồn 3.3V |
| **D0** (SCK) | **D18** (GPIO 18) | Hàng bên phải bo |
| **D1** (MOSI) | **D23** (GPIO 23) | Góc trên cùng bên phải |
| **RES** | **D4** (GPIO 4) | Hàng bên phải bo |
| **DC** | **D16** (RX2) | Hàng bên phải bo |
| **CS** | **D5** (GPIO 5) | Hàng bên phải bo |

---

## 2. 4 Cụm đèn xe ô tô (Chân GND nối chung cực âm)

| Cụm đèn giao thông | Đèn ĐỎ (Red) | Đèn VÀNG (Yellow) | Đèn XANH (Green) | Chân GND (COM) |
| :--- | :--- | :--- | :--- | :--- |
| **Cụm 1: BẮC** | **D13** | **D15** | **D14** | Nối vào GND chung |
| **Cụm 2: NAM** | **D32** | **D33** | **D19** | Nối vào GND chung |
| **Cụm 3: ĐÔNG** | **D25** | **D26** | **D27** | Nối vào GND chung |
| **Cụm 4: TÂY** | **D21** | **D22** | **D17** *(in chữ TX2 hoặc D17)* | Nối vào GND chung |

---

## 3. Lưu ý khi cắm dây:
- **Chân GND:** Cả 4 module đèn và OLED đều cắm chung vào 1 đường dài màu xanh `(-)` trên Breadboard, sau đó nối 1 sợi dây từ đường đó về chân `GND` của ESP32.
- **Chân D2:** Là chân điều khiển Đèn Vàng nhánh Bắc. Chân này nằm ngay cạnh chân `D4` ở hàng bên phải của ESP32 DevKit V1.
