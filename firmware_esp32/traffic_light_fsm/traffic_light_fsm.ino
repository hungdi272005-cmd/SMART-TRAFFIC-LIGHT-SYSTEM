/*
 * HỆ THỐNG ĐÈN GIAO THÔNG THÍCH ỨNG THỜI GIAN THỰC (NHÓM 11)
 * FIRMWARE ĐIỀU KHIỂN ESP32 (4 CỤM ĐÈN + OLED SPI + MQTT + FSM NON-BLOCKING)
 * 
 * PHIÊN BẢN ĐÃ TỐI ƯU (BỎ ĐÈN ĐI BỘ - DỄ CẮM CHÂN 100%):
 * - Màn hình OLED SPI: D0(18), D1(23), RES(4), DC(16), CS(5)
 * - Đèn Bắc: Đỏ(13), Vàng(2) [Dùng D2 có sẵn trên bo], Xanh(14)
 * - Đèn Đông: Đỏ(25), Vàng(26), Xanh(27)
 * - Đèn Nam: Đỏ(32), Vàng(33), Xanh(19)
 * - Đèn Tây: Đỏ(21), Vàng(22), Xanh(17)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- 1. CẤU HÌNH WIFI & MQTT ---
const char* WIFI_SSID     = "201";       // Thay bằng tên Wi-Fi nhà/phòng bạn
const char* WIFI_PASSWORD = "46478405";          // Thay bằng mật khẩu Wi-Fi
const char* MQTT_SERVER   = "192.168.0.103";           // Địa chỉ IP của Laptop chạy Mosquitto Broker
const int   MQTT_PORT     = 1883;
const char* TOPIC_TIMING  = "traffic/sa_ban/timing";

// --- 2. CẤU HÌNH MÀN HÌNH OLED SPI 0.96 INCH (7 CHÂN) ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_MOSI   23  // Chân D1 trên OLED nối D23
#define OLED_CLK    18  // Chân D0 trên OLED nối D18
#define OLED_DC     16  // Chân DC trên OLED nối D16 (RX2)
#define OLED_CS      5  // Chân CS trên OLED nối D5
#define OLED_RESET   4  // Chân RES trên OLED nối D4

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, OLED_MOSI, OLED_CLK, OLED_DC, OLED_RESET, OLED_CS);

// --- 3. ĐỊNH NGHĨA CHÂN GPIO CHO 4 CỤM ĐÈN XE ---
// Cụm 1: Hướng BẮC (Pha 1)
#define NORTH_RED     13  // Chân D13
#define NORTH_YELLOW  15  // Chân D15
#define NORTH_GREEN   14  // Chân D14

// Cụm 2: Hướng NAM (Pha 1)
#define SOUTH_RED     32  // Chân D32
#define SOUTH_YELLOW  33  // Chân D33
#define SOUTH_GREEN   19  // Chân D19

// Cụm 3: Hướng ĐÔNG (Pha 2)
#define EAST_RED      25  // Chân D25
#define EAST_YELLOW   26  // Chân D26
#define EAST_GREEN    27  // Chân D27

// Cụm 4: Hướng TÂY (Pha 2)
#define WEST_RED      21  // Chân D21
#define WEST_YELLOW   22  // Chân D22
#define WEST_GREEN    17  // Chân D17 (TX2)

// --- 4. MÁY TRẠNG THÁI HỮU HẠN (FSM) & BỘ ĐỆM ĐÔI ---
enum TrafficState {
  STATE_PHASE1_GREEN,   // Bắc-Nam Xanh, Đông-Tây Đỏ
  STATE_PHASE1_YELLOW,  // Bắc-Nam Vàng, Đông-Tây Đỏ
  STATE_PHASE2_GREEN,   // Bắc-Nam Đỏ, Đông-Tây Xanh
  STATE_PHASE2_YELLOW   // Bắc-Nam Đỏ, Đông-Tây Vàng
};

TrafficState currentState = STATE_PHASE1_GREEN;

// Active Buffer: Đang chạy trong chu kỳ thực tế
int activeGreen1 = 15;
int activeGreen2 = 15;
int activeYellow = 3;

// Shadow Buffer: Nhận từ MQTT (chờ nạp)
int pendingGreen1 = 15;
int pendingGreen2 = 15;
int pendingYellow = 3;

// Biến lưu số xe đếm được từ AI
int currentN1 = 0;
int currentN2 = 0;

// Bộ đếm lùi thời gian bằng millis() (Non-blocking)
unsigned long previousMillis = 0;
int countdown = 0;

// Failsafe Watchdog: Quá 15s không có MQTT -> Chạy cố định
unsigned long lastMqttReceiveTime = 0;
const unsigned long FAILSAFE_TIMEOUT_MS = 15000;

WiFiClient espClient;
PubSubClient client(espClient);

// --- HÀM BẬT/TẮT 4 CỤM ĐÈN ---
void setLights(bool n_r, bool n_y, bool n_g,
               bool s_r, bool s_y, bool s_g,
               bool e_r, bool e_y, bool e_g,
               bool w_r, bool w_y, bool w_g) {
  digitalWrite(NORTH_RED, n_r);
  digitalWrite(NORTH_YELLOW, n_y);
  digitalWrite(NORTH_GREEN, n_g);

  digitalWrite(SOUTH_RED, s_r);
  digitalWrite(SOUTH_YELLOW, s_y);
  digitalWrite(SOUTH_GREEN, s_g);

  digitalWrite(EAST_RED, e_r);
  digitalWrite(EAST_YELLOW, e_y);
  digitalWrite(EAST_GREEN, e_g);

  digitalWrite(WEST_RED, w_r);
  digitalWrite(WEST_YELLOW, w_y);
  digitalWrite(WEST_GREEN, w_g);
}

// --- CẬP NHẬT GIAO DIỆN OLED RÕ NÉT (ĐÃ BỎ ĐI BỘ) ---
void updateOLED() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  // Tiêu đề
  display.setTextSize(1);
  display.setCursor(4, 2);
  display.print(F("SMART TRAFFIC - NHOM11"));
  display.drawLine(0, 12, 128, 12, SSD1306_WHITE);

  // Chế độ hoạt động
  display.setCursor(4, 16);
  if (millis() - lastMqttReceiveTime > FAILSAFE_TIMEOUT_MS) {
    display.print(F("MODE: FAILSAFE (15s)"));
  } else {
    display.print(F("MODE: AI ADAPTIVE (OK)"));
  }

  // Hiển thị trạng thái & đếm giây từng trục
  display.setCursor(4, 28);
  switch (currentState) {
    case STATE_PHASE1_GREEN:
      display.printf("BAC-NAM : XANH [%2ds]\n", countdown);
      display.setCursor(4, 40);
      display.printf("DONG-TAY:  DO  [%2ds]", countdown + activeYellow);
      break;
    case STATE_PHASE1_YELLOW:
      display.printf("BAC-NAM : VANG [%2ds]\n", countdown);
      display.setCursor(4, 40);
      display.printf("DONG-TAY:  DO  [%2ds]", countdown);
      break;
    case STATE_PHASE2_GREEN:
      display.printf("BAC-NAM :  DO  [%2ds]\n", countdown + activeYellow);
      display.setCursor(4, 40);
      display.printf("DONG-TAY: XANH [%2ds]", countdown);
      break;
    case STATE_PHASE2_YELLOW:
      display.printf("BAC-NAM :  DO  [%2ds]\n", countdown);
      display.setCursor(4, 40);
      display.printf("DONG-TAY: VANG [%2ds]", countdown);
      break;
  }

  // Dòng đáy: Số xe AI đếm được
  display.drawLine(0, 51, 128, 51, SSD1306_WHITE);
  display.setCursor(4, 54);
  display.printf("Xe AI: N1=%d | N2=%d", currentN1, currentN2);

  display.display();
}

// --- XỬ LÝ GÓI TIN MQTT TỪ BACKEND PYTHON ---
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String jsonStr;
  for (unsigned int i = 0; i < length; i++) {
    jsonStr += (char)payload[i];
  }

  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, jsonStr);
  if (!error) {
    pendingGreen1 = doc["green1"] | 15;
    pendingGreen2 = doc["green2"] | 15;
    pendingYellow = doc["yellow"] | 3;
    currentN1     = doc["n1"] | 0;
    currentN2     = doc["n2"] | 0;
    lastMqttReceiveTime = millis();
  }
}

// --- KẾT NỐI WIFI & MQTT ---
void setupWiFi() {
  Serial.print("Ket noi WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int count = 0;
  while (WiFi.status() != WL_CONNECTED && count < 20) {
    delay(400);
    Serial.print(".");
    count++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi OK! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nChua ket noi WiFi -> Chay Failsafe.");
  }
}

void reconnectMQTT() {
  if (!client.connected() && WiFi.status() == WL_CONNECTED) {
    if (client.connect("ESP32_Traffic_Group11")) {
      client.subscribe(TOPIC_TIMING);
    }
  }
}

void setup() {
  Serial.begin(115200);

  // Cấu hình chân đèn xe là ngõ ra OUTPUT
  pinMode(NORTH_RED, OUTPUT); pinMode(NORTH_YELLOW, OUTPUT); pinMode(NORTH_GREEN, OUTPUT);
  pinMode(SOUTH_RED, OUTPUT); pinMode(SOUTH_YELLOW, OUTPUT); pinMode(SOUTH_GREEN, OUTPUT);
  pinMode(EAST_RED, OUTPUT);  pinMode(EAST_YELLOW, OUTPUT);  pinMode(EAST_GREEN, OUTPUT);
  pinMode(WEST_RED, OUTPUT);  pinMode(WEST_YELLOW, OUTPUT);  pinMode(WEST_GREEN, OUTPUT);

  // Khởi động OLED SPI
  if (display.begin(SSD1306_SWITCHCAPVCC)) {
    display.clearDisplay();
    display.display();
  }

  // Kết nối mạng
  setupWiFi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(mqttCallback);

  // Bắt đầu chu kỳ
  countdown = activeGreen1;
  previousMillis = millis();
}

void loop() {
  // Duy trì kết nối MQTT
  if (!client.connected()) {
    static unsigned long lastReconnect = 0;
    if (millis() - lastReconnect > 5000) {
      lastReconnect = millis();
      reconnectMQTT();
    }
  } else {
    client.loop();
  }

  // --- MÁY TRẠNG THÁI HỮU HẠN FSM (ĐẾM LÙI TỪNG GIÂY) ---
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= 1000) {
    previousMillis = currentMillis;
    countdown--;

    if (countdown <= 0) {
      switch (currentState) {
        case STATE_PHASE1_GREEN:
          currentState = STATE_PHASE1_YELLOW;
          countdown = activeYellow;
          break;

        case STATE_PHASE1_YELLOW:
          currentState = STATE_PHASE2_GREEN;
          countdown = activeGreen2;
          break;

        case STATE_PHASE2_GREEN:
          currentState = STATE_PHASE2_YELLOW;
          countdown = activeYellow;
          break;

        case STATE_PHASE2_YELLOW:
          currentState = STATE_PHASE1_GREEN;
          // DOUBLE BUFFERING: Đổi sang thời gian mới nhất từ AI khi xong 1 vòng
          activeGreen1 = pendingGreen1;
          activeGreen2 = pendingGreen2;
          activeYellow = pendingYellow;
          countdown = activeGreen1;
          break;
      }
    }

    updateOLED();
  }

  // --- ĐIỀU KHIỂN CÁC ĐÈN THEO PHA ---
  switch (currentState) {
    case STATE_PHASE1_GREEN:
      // Bắc-Nam: XANH | Đông-Tây: ĐỎ
      setLights(LOW, LOW, HIGH,
                LOW, LOW, HIGH,
                HIGH, LOW, LOW,
                HIGH, LOW, LOW);
      break;

    case STATE_PHASE1_YELLOW:
      // Bắc-Nam: VÀNG | Đông-Tây: ĐỎ
      setLights(LOW, HIGH, LOW,
                LOW, HIGH, LOW,
                HIGH, LOW, LOW,
                HIGH, LOW, LOW);
      break;

    case STATE_PHASE2_GREEN:
      // Bắc-Nam: ĐỎ | Đông-Tây: XANH
      setLights(HIGH, LOW, LOW,
                HIGH, LOW, LOW,
                LOW, LOW, HIGH,
                LOW, LOW, HIGH);
      break;

    case STATE_PHASE2_YELLOW:
      // Bắc-Nam: ĐỎ | Đông-Tây: VÀNG
      setLights(HIGH, LOW, LOW,
                HIGH, LOW, LOW,
                LOW, HIGH, LOW,
                LOW, HIGH, LOW);
      break;
  }
}
