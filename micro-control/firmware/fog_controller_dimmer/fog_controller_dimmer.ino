// =============================================================
// fog_controller_dimmer.ino - 細かい調光版
//
// キー操作(シリアルモニタ 115200):
//   w ... 明るさ +5%
//   s ... 明るさ -5%
//   e ... 明るさ +1%(微調整)
//   d ... 明るさ -1%(微調整)
//   数字(例: 45) ... その明るさに直接ジャンプ(0〜100)
//   0 ... 消灯
//   f ... 全開(100%)
//
// 例: "w w w" と打てば +15%。"70" と打てば70%へ。
// =============================================================

// ---------- 設定 ----------
const int PIN_PWM = 4;        // → BTS7960 RPWM
const int PIN_EN  = 5;        // → BTS7960 R_EN・L_EN

const int PWM_FREQ = 200;     // ハロゲン用
const int PWM_RES  = 12;      // 0〜4095

const float GAMMA = 0.5;      // ハロゲン用の体感補正
const uint32_t RAMP_MS = 300; // ソフトスタート

const int STEP_BIG   = 5;     // w/s の増減幅(%)
const int STEP_SMALL = 1;     // e/d の増減幅(%)

const int MAX_DUTY_PCT = 100; // バッテリー電源+④⑤⑥合格済みなら100でOK
                              // 5A級ACアダプタに戻すときは80へ
// ---------------------------

const int DUTY_MAX = (1 << PWM_RES) - 1;
const int DUTY_CAP = (int)((long)DUTY_MAX * MAX_DUTY_PCT / 100);

int levelPct = 0;          // 現在の明るさ(体感% 0〜100)
float currentDuty = 0;
uint32_t lastLoopMs = 0;

String numBuf = "";        // 数値直接入力用のバッファ

int targetDuty() {
  if (levelPct <= 0) return 0;
  float norm = levelPct / 100.0f;
  int duty = (int)(powf(norm, GAMMA) * DUTY_MAX);
  return min(duty, DUTY_CAP);
}

void printStatus() {
  // 現在値をバー表示付きで出す(シリアルモニタで見やすい)
  int bars = levelPct / 5;
  Serial.printf("明るさ %3d%% [", levelPct);
  for (int i = 0; i < 20; i++) Serial.print(i < bars ? "#" : "-");
  Serial.printf("] duty %d/%d\n", targetDuty(), DUTY_MAX);
}

void setLevel(int pct) {
  levelPct = constrain(pct, 0, 100);
  printStatus();
}

void commitNumBuf() {
  if (numBuf.length() > 0) {
    setLevel(numBuf.toInt());
    numBuf = "";
  }
}

void handleKeys() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c >= '1' && c <= '9') { numBuf += c; continue; }
    if (c == '0') {
      if (numBuf.length() > 0) { numBuf += c; continue; }  // "10"等の一部
      setLevel(0);  // 単独の0は消灯
      continue;
    }

    // 数字以外のキーが来たら、溜まっている数値を確定
    commitNumBuf();

    switch (c) {
      case 'w': setLevel(levelPct + STEP_BIG);   break;
      case 's': setLevel(levelPct - STEP_BIG);   break;
      case 'e': setLevel(levelPct + STEP_SMALL); break;
      case 'd': setLevel(levelPct - STEP_SMALL); break;
      case 'f': setLevel(100); break;
      case '\n': case '\r': case ' ': break;  // 区切り文字は無視
      default: break;
    }
  }
}

void updateOutput() {
  uint32_t now = millis();
  float dt = (now - lastLoopMs);
  lastLoopMs = now;

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

  pinMode(PIN_EN, OUTPUT);
  digitalWrite(PIN_EN, LOW);

  ledcAttach(PIN_PWM, PWM_FREQ, PWM_RES);
  ledcWrite(PIN_PWM, 0);

  digitalWrite(PIN_EN, HIGH);

  lastLoopMs = millis();
  Serial.println("=== fog_controller dimmer ===");
  Serial.println("w:+5% s:-5% e:+1% d:-1% f:全開 0:消灯 数字:直接指定(例 45)");
}

void loop() {
  handleKeys();
  updateOutput();
  delay(1);
}
