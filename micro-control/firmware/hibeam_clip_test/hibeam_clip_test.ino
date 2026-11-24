// ハイビーム左右 クリップ直結実験用 (HW-039 1枚, M+=右, M-=左)
// シリアル(115200)コマンド:
//   r<0-100>  右の明るさ(体感%)   例: r30
//   l<0-100>  左の明るさ(体感%)   例: l30
//   b<0-100>  左右同時            例: b50
//   0         全消灯
//   t<ms>     フェード時間(0-100%にかかる時間)  例: t800
// 安全要件: 起動時EN=LOW・明るさ0%、全準備後にEN=HIGH、MAX_DUTY_PCTでcap

#include <Arduino.h>

const int PIN_RPWM = 4;   // 右 (M+)
const int PIN_LPWM = 6;   // 左 (M-)  ※予約GPIO6を使用
const int PIN_EN   = 5;   // R_EN + L_EN

const uint32_t PWM_FREQ = 1000;   // LED想定
const uint8_t  PWM_RES  = 12;     // 0-4095
const float    GAMMA    = 2.2f;   // LED=2.2 / ハロゲン=0.5
const float    MAX_DUTY_PCT = 100.0f;
uint32_t rampMs = 300;            // 0->100% にかかる時間。減光は2倍速

struct Ch { int pin; float target; float cur; };
Ch ch[2] = { {PIN_RPWM, 0, 0}, {PIN_LPWM, 0, 0} };

uint32_t toDuty(float pct) {
  if (pct <= 0) return 0;
  float d = powf(pct / 100.0f, GAMMA) * 4095.0f;
  float cap = 4095.0f * MAX_DUTY_PCT / 100.0f;
  if (d > cap) d = cap;
  return (uint32_t)(d + 0.5f);
}

void setup() {
  pinMode(PIN_EN, OUTPUT);
  digitalWrite(PIN_EN, LOW);               // 起動時の誤点灯防止
  pinMode(PIN_RPWM, OUTPUT); digitalWrite(PIN_RPWM, LOW);
  pinMode(PIN_LPWM, OUTPUT); digitalWrite(PIN_LPWM, LOW);

  Serial.begin(115200);
  ledcAttach(PIN_RPWM, PWM_FREQ, PWM_RES);
  ledcAttach(PIN_LPWM, PWM_FREQ, PWM_RES);
  ledcWrite(PIN_RPWM, 0);
  ledcWrite(PIN_LPWM, 0);

  delay(200);
  digitalWrite(PIN_EN, HIGH);              // 全準備完了後に出力許可
  Serial.println("hibeam_clip_test ready. r<%> l<%> b<%> 0 t<ms>");
}

void handleLine(String s) {
  s.trim();
  if (s.length() == 0) return;
  char c = s.charAt(0);
  int v = s.substring(1).toInt();
  if (c == '0' && s.length() == 1) { ch[0].target = ch[1].target = 0; }
  else if (c == 'r') ch[0].target = constrain(v, 0, 100);
  else if (c == 'l') ch[1].target = constrain(v, 0, 100);
  else if (c == 'b') ch[0].target = ch[1].target = constrain(v, 0, 100);
  else if (c == 't') rampMs = constrain(v, 0, 10000);
  else { Serial.println("? r<%> l<%> b<%> 0 t<ms>"); return; }
  Serial.printf("target R=%.0f%% L=%.0f%% ramp=%ums\n", ch[0].target, ch[1].target, rampMs);
}

void loop() {
  static String buf;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { handleLine(buf); buf = ""; }
    else buf += c;
  }

  static uint32_t last = millis();
  uint32_t now = millis();
  float dt = (float)(now - last);
  last = now;

  for (auto &k : ch) {
    float step = (rampMs == 0) ? 100.0f : 100.0f * dt / rampMs;
    if (k.cur < k.target)      k.cur = min(k.target, k.cur + step);
    else if (k.cur > k.target) k.cur = max(k.target, k.cur - step * 2);  // 減光は2倍速
    ledcWrite(k.pin, toDuty(k.cur));
  }
  delay(2);
}
