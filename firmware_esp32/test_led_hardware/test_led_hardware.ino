/*
 * TEST PHẦN CỨNG ĐÈN GIAO THÔNG - NHÓM 11
 * Mục đích: Kiểm tra các mối nối dây LED với ESP32 xem có sáng đủ các màu không.
 */

// Định nghĩa chân GPIO theo sơ đồ đã quy ước
#define P1_RED    25  // Pha 1 (Trục Dọc) - Đỏ (Đèn 1 & 2)
#define P1_YELLOW 26  // Pha 1 (Trục Dọc) - Vàng (Đèn 1 & 2)
#define P1_GREEN  27  // Pha 1 (Trục Dọc) - Xanh (Đèn 1 & 2)

#define P2_RED    14  // Pha 2 (Trục Ngang) - Đỏ (Đèn 3)
#define P2_YELLOW 12  // Pha 2 (Trục Ngang) - Vàng (Đèn 3)
#define P2_GREEN  13  // Pha 2 (Trục Ngang) - Xanh (Đèn 3)

void setup() {
  Serial.begin(115200);
  Serial.println("--- DANG TEST PHAN CUNG DEN GIAO THONG ESP32 ---");

  // Thiết lập các chân xuất tín hiệu OUTPUT
  pinMode(P1_RED, OUTPUT);
  pinMode(P1_YELLOW, OUTPUT);
  pinMode(P1_GREEN, OUTPUT);

  pinMode(P2_RED, OUTPUT);
  pinMode(P2_YELLOW, OUTPUT);
  pinMode(P2_GREEN, OUTPUT);

  // Tắt toàn bộ đèn ban đầu
  tatHetDen();
}

void loop() {
  // 1. Test Pha 1 (Trục Dọc): Lần lượt Xanh -> Vàng -> Đỏ
  Serial.println("Pha 1: Bat den XANH");
  tatHetDen();
  digitalWrite(P1_GREEN, HIGH);
  delay(1500);

  Serial.println("Pha 1: Bat den VANG");
  tatHetDen();
  digitalWrite(P1_YELLOW, HIGH);
  delay(1000);

  Serial.println("Pha 1: Bat den DO");
  tatHetDen();
  digitalWrite(P1_RED, HIGH);
  delay(1500);

  // 2. Test Pha 2 (Trục Ngang): Lần lượt Xanh -> Vàng -> Đỏ
  Serial.println("Pha 2: Bat den XANH");
  tatHetDen();
  digitalWrite(P2_GREEN, HIGH);
  delay(1500);

  Serial.println("Pha 2: Bat den VANG");
  tatHetDen();
  digitalWrite(P2_YELLOW, HIGH);
  delay(1000);

  Serial.println("Pha 2: Bat den DO");
  tatHetDen();
  digitalWrite(P2_RED, HIGH);
  delay(1500);

  // 3. Test sang dong thoi tat ca cac den
  Serial.println("Test: BAT TAT CA CAC DEN");
  digitalWrite(P1_RED, HIGH);
  digitalWrite(P1_YELLOW, HIGH);
  digitalWrite(P1_GREEN, HIGH);
  digitalWrite(P2_RED, HIGH);
  digitalWrite(P2_YELLOW, HIGH);
  digitalWrite(P2_GREEN, HIGH);
  delay(2000);

  tatHetDen();
  delay(1000);
}

void tatHetDen() {
  digitalWrite(P1_RED, LOW);
  digitalWrite(P1_YELLOW, LOW);
  digitalWrite(P1_GREEN, LOW);
  digitalWrite(P2_RED, LOW);
  digitalWrite(P2_YELLOW, LOW);
  digitalWrite(P2_GREEN, LOW);
}
