// =============================================================
// fog_controller_simple.ino - シンプル版(MIDIなし)
//
// PCのキーボードで操作する:
//   Arduino IDEのシリアルモニタに文字を打って送信するだけ
//     "1" ... 弱(30%)で点灯。もう一度 "1" で消灯(トグル)
//     "2" ... 強(100%)で点灯。もう一度 "2" で消灯(トグル)
//     "0" ... 即消灯
//
// MIDI版からの簡略化:
//   - ライブラリ不要(標準機能のみ)
//   - Tools > USB Mode の変更も不要(デフォルトのまま)
//   - USBケーブルは書き込み用の1本だけ。それが操作線を兼ねる
//
// 配線は設計書 rev.C/D §2 と同一(RPWM=GPIO4, EN=GPIO5)
// ボード: ESP32S3 Dev Module / シリアルモニタは 115200bps
// =============================================================

// ---------- 設定 ----------
const int PIN_PWM = 4;        // → BTS7960 RPWM
const int PIN_EN  = 5;        // → BTS7960 R_EN・L_EN(束ね)

const int PWM_FREQ = 200;     // ハロゲン用。LED化したら1000へ
const int PWM_RES  = 12;      // デューティ 0〜4095

const float GAMMA = 0.5;      // ハロゲン用の体感補正
const uint32_t RAMP_MS = 300; // ソフトスタート(ハロゲンでは必須)

const int LEVEL_LOW_PCT  = 30;   // キー"1"の明るさ(体感%)
const int LEVEL_HIGH_PCT = 100;  // キー"2"の明るさ(体感%)

// 電源容量に応じたソフト上限(設計書rev.D §6)
//   テスト灯+5Aアダプタ=100 / ハロゲン1灯+5Aアダプタ=80
const int MAX_DUTY_PCT = 80;
// ---------------------------

const int DUTY_MAX = (1 << PWM_RES) - 1;
const int DUTY_CAP = (int)((long)DUTY_MAX * MAX_DUTY_PCT / 100);

int levelPct = 0;          // 現在の設定(0=消灯, 30, 100)
float currentDuty = 0;     // ソフトスタート用の現在値
uint32_t lastLoopMs = 0;

// 体感%(0〜100) → 目標デューティ(ガンマ補正+上限)
int targetDuty() {
  if (levelPct <= 0) return 0;
  float norm = levelPct / 100.0f;
  int duty = (int)(powf(norm, GAMMA) * DUTY_MAX);
  return min(duty, DUTY_CAP);
}

void setLevel(int pct, const char* label) {
  // 同じレベルをもう一度指定したら消灯(トグル)
  if (levelPct == pct) {
    levelPct = 0;
    Serial.printf("[key] %s をもう一度 -> 消灯\n", label);
  } else {
    levelPct = pct;
    Serial.printf("[key] %s -> %d%% (duty %d/%d)\n",
                  label, pct, targetDuty(), DUTY_MAX);
  }
}

void handleKeys() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    switch (c) {
      case '1': setLevel(LEVEL_LOW_PCT,  "1:弱"); break;
      case '2': setLevel(LEVEL_HIGH_PCT, "2:強"); break;
      case '0':
        levelPct = 0;
        Serial.println("[key] 0 -> 即消灯");
        break;
      default:
        break;  // 改行コード等は無視
    }
  }
}

void updateOutput() {
  uint32_t now = millis();
  float dt = (now - lastLoopMs);
  lastLoopMs = now;

  // ソフトスタート: 目標へ一定速度でしか変化させない
  float maxStep = (DUTY_MAX / (float)RAMP_MS) * dt;
  float target = targetDuty();

  if (currentDuty < target) {
    currentDuty = min(currentDuty + maxStep, target);
  } else if (currentDuty > target) {
    currentDuty = max(currentDuty - maxStep * 2, target);
  }

  ledcWrite(PIN_PWM, (int)currentDuty);
}

void setup() {
  Serial.begin(115200);

  // EN=LOWで起動 → FETを眠らせたまま準備
  pinMode(PIN_EN, OUTPUT);
  digitalWrite(PIN_EN, LOW);

  ledcAttach(PIN_PWM, PWM_FREQ, PWM_RES);
  ledcWrite(PIN_PWM, 0);

  digitalWrite(PIN_EN, HIGH);  // 準備完了、FET許可

  lastLoopMs = millis();
  Serial.println("=== fog_controller simple ===");
  Serial.println("キー操作: 1=弱(30%) / 2=強(100%) / 0=消灯");
  Serial.println("同じキーをもう一度押すと消灯します");
}

void loop() {
  handleKeys();
  updateOutput();
  delay(1);
}
