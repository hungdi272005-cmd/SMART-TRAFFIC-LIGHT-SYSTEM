/*
 * TEST TOÀN BỘ PHẦN CỨNG (4 CỤM ĐÈN + OLED SPI) - NHÓM 11
 * Mục đích: Kiểm tra từng bóng LED và màn hình OLED để đảm bảo cắm đúng 100%.
 */

#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- CẤU HÌNH OLED SPI ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_MOSI   23  // D1
#define OLED_CLK    18  // D0
#define OLED_DC     16  // DC
#define OLED_CS      5  // CS
#define OLED_RESET   4  // RES

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, OLED_MOSI, OLED_CLK, OLED_DC, OLED_RESET, OLED_CS);

// --- CHÂN 4 CỤM ĐÈN ---
#define NORTH_RED     13
#define NORTH_YELLOW  15
#define NORTH_GREEN   14

#define SOUTH_RED     32
#define SOUTH_YELLOW  33
#define SOUTH_GREEN   19

#define EAST_RED      25
#define EAST_YELLOW   26
#define EAST_GREEN    27

#define WEST_RED      21
#define WEST_YELLOW   22
#define WEST_GREEN    17

void tatHet() {
  digitalWrite(NORTH_RED, LOW); digitalWrite(NORTH_YELLOW, LOW); digitalWrite(NORTH_GREEN, LOW);
  digitalWrite(SOUTH_RED, LOW); digitalWrite(SOUTH_YELLOW, LOW); digitalWrite(SOUTH_GREEN, LOW);
  digitalWrite(EAST_RED, LOW);  digitalWrite(EAST_YELLOW, LOW);  digitalWrite(EAST_GREEN, LOW);
  digitalWrite(WEST_RED, LOW);  digitalWrite(WEST_YELLOW, LOW);  digitalWrite(WEST_GREEN, LOW);
}

void setup() {
  Serial.begin(115200);
  Serial.println("=== BAT DAU TEST PHAN CUNG ===");

  pinMode(NORTH_RED, OUTPUT); pinMode(NORTH_YELLOW, OUTPUT); pinMode(NORTH_GREEN, OUTPUT);
  pinMode(SOUTH_RED, OUTPUT); pinMode(SOUTH_YELLOW, OUTPUT); pinMode(SOUTH_GREEN, OUTPUT);
  pinMode(EAST_RED, OUTPUT);  pinMode(EAST_YELLOW, OUTPUT);  pinMode(EAST_GREEN, OUTPUT);
  pinMode(WEST_RED, OUTPUT);  pinMode(WEST_YELLOW, OUTPUT);  pinMode(WEST_GREEN, OUTPUT);

  tatHet();

  // Test OLED
  if (display.begin(SSD1306_SWITCHCAPVCC)) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(10, 15);
    display.println(F("SMART TRAFFIC SYSTEM"));
    display.setCursor(20, 32);
    display.println(F("TEST HARDWARE OK!"));
    display.setCursor(35, 48);
    display.println(F("NHOM 11"));
    display.display();
  }
}

void loop() {
  // 1. Test lần lượt từng hướng
  Serial.println("1. Test Cum BAC: Do -> Vang -> Xanh");
  tatHet(); digitalWrite(NORTH_RED, HIGH); delay(600);
  tatHet(); digitalWrite(NORTH_YELLOW, HIGH); delay(600);
  tatHet(); digitalWrite(NORTH_GREEN, HIGH); delay(600);

  Serial.println("2. Test Cum NAM: Do -> Vang -> Xanh");
  tatHet(); digitalWrite(SOUTH_RED, HIGH); delay(600);
  tatHet(); digitalWrite(SOUTH_YELLOW, HIGH); delay(600);
  tatHet(); digitalWrite(SOUTH_GREEN, HIGH); delay(600);

  Serial.println("3. Test Cum DONG: Do -> Vang -> Xanh");
  tatHet(); digitalWrite(EAST_RED, HIGH); delay(600);
  tatHet(); digitalWrite(EAST_YELLOW, HIGH); delay(600);
  tatHet(); digitalWrite(EAST_GREEN, HIGH); delay(600);

  Serial.println("4. Test Cum TAY: Do -> Vang -> Xanh");
  tatHet(); digitalWrite(WEST_RED, HIGH); delay(600);
  tatHet(); digitalWrite(WEST_YELLOW, HIGH); delay(600);
  tatHet(); digitalWrite(WEST_GREEN, HIGH); delay(600);

  // 2. Sáng toàn bộ đèn cùng lúc trong 2 giây
  Serial.println("5. BAT TAT CA CAC BONG DEN");
  digitalWrite(NORTH_RED, HIGH); digitalWrite(NORTH_YELLOW, HIGH); digitalWrite(NORTH_GREEN, HIGH);
  digitalWrite(SOUTH_RED, HIGH); digitalWrite(SOUTH_YELLOW, HIGH); digitalWrite(SOUTH_GREEN, HIGH);
  digitalWrite(EAST_RED, HIGH);  digitalWrite(EAST_YELLOW, HIGH);  digitalWrite(EAST_GREEN, HIGH);
  digitalWrite(WEST_RED, HIGH);  digitalWrite(WEST_YELLOW, HIGH);  digitalWrite(WEST_GREEN, HIGH);
  delay(2000);

  tatHet();
  delay(1000);
}
