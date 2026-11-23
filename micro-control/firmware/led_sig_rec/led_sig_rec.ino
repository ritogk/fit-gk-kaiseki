// led_sig_rec — GK前期 純正LEDロービーム駆動ユニットの信号線を記録する (ESP32-S3)
//
// 目的: 車側カプラーの信号ピン(Y、予備でX)の High/Low の時間を µs 単位で記録し、
//       シリアルへ出す。解析は tools/ledsig.py analyze で行う。
//
// RMT ではなく「エッジ割り込み + µs タイムスタンプ」で取る理由:
//   - RMT RX は1区間が最大約32ms(15bit @1MHz)で、それより長い High/Low や
//     一定レベル(PWMでない信号)を区間として取れない
//   - RMT RX のメモリ(48シンボル/ブロック)を超えるフレームは切り捨てられる
//   割り込み方式は 〜100kHz 程度までのエッジなら µs 精度で取れる。
//   それより速い信号だと overflow/取りこぼしが出るので、その場合はロジアナを使う。
//
// ── 配線 ─────────────────────────────────────────────
//   車側カプラー                       ESP32-S3
//   信号Y ──[10kΩ]──┬──────────────── GPIO10 (CH Y)
//                    ├─[20kΩ]─ GND
//                    └─[ツェナー3.3V]─ GND (カソードをGPIO側)
//   信号X ──(同じ回路)──────────────── GPIO11 (CH X, 予備)
//   GND(確定ピン) ───────────────────── GND
//   ※ 分圧は「上10k / 下20k」(5V→3.3V、12V→8V→ツェナーで3.3Vに制限)。
//     「上20k / 下10k」だと5Vが1.67Vになり、ESP32のHigh判定(約2.5V)に届かない。
//   ※ ユニットはつないだまま、カプラー裏からピンを当てて測る(バックプローブ)。
//     信号がオープンコレクタだと、ユニット側のプルアップが無いと波形が出ない(推測)。
// ────────────────────────────────────────────────────
//
// シリアル(115200)コマンド。1行で送る:
//   c <label> [ms]  記録(既定1000ms、最大5000ms)。例: c lo_on 1000
//   m               ライブ表示の ON/OFF(0.5秒ごとに各CHのレベルとエッジ数)
//   ?               ヘルプ
//
// 出力形式(ledsig.py が読む):
//   #CAP label=lo_on ms=1000 Y0=1 X0=0 edges=1234 overflow=0
//   Y H 123        … CH Y が High だった時間 123µs
//   Y L 456
//   *Y H 789       … 先頭/末尾の区間は記録窓で切れているので * 付き
//   #END
// 入力は「分圧のみ」で反転しない。H = 車側の信号が High。

#include <Arduino.h>

static const uint8_t PIN_Y = 10;
static const uint8_t PIN_X = 11;
static const uint32_t MAX_EDGES = 16384;

struct Edge { uint32_t t; uint8_t ch; uint8_t lvl; };
static Edge *edges;
static volatile uint32_t nEdges = 0;
static volatile bool capturing = false;
static volatile uint32_t overflow = 0;
static volatile uint32_t liveCnt[2] = {0, 0};

static void IRAM_ATTR onEdge(uint8_t ch, uint8_t pin) {
  uint32_t t = (uint32_t)esp_timer_get_time();
  uint8_t lvl = digitalRead(pin);
  liveCnt[ch]++;
  if (!capturing) return;
  uint32_t n = nEdges;
  if (n >= MAX_EDGES) { overflow++; return; }
  edges[n] = {t, ch, lvl};
  nEdges = n + 1;
}
static void IRAM_ATTR isrY() { onEdge(0, PIN_Y); }
static void IRAM_ATTR isrX() { onEdge(1, PIN_X); }

static const char CH_NAME[2] = {'Y', 'X'};

static void emitChannel(uint8_t ch, uint8_t lvl0, uint32_t t0, uint32_t t1) {
  // 区間を組み立てる。同じレベルが続くエッジ(グリッチ取りこぼし)は前の区間に含める
  uint8_t lvl = lvl0;
  uint32_t segStart = t0;
  bool first = true;
  for (uint32_t i = 0; i < nEdges; i++) {
    if (edges[i].ch != ch) continue;
    if (edges[i].lvl == lvl) continue;
    Serial.printf("%s%c %c %lu\n", first ? "*" : "", CH_NAME[ch], lvl ? 'H' : 'L',
                  (unsigned long)(edges[i].t - segStart));
    first = false;
    lvl = edges[i].lvl;
    segStart = edges[i].t;
  }
  Serial.printf("*%c %c %lu\n", CH_NAME[ch], lvl ? 'H' : 'L', (unsigned long)(t1 - segStart));
}

static void capture(const String &label, uint32_t ms) {
  ms = constrain(ms, 10UL, 5000UL);
  nEdges = 0; overflow = 0;
  uint8_t y0 = digitalRead(PIN_Y), x0 = digitalRead(PIN_X);
  uint32_t t0 = (uint32_t)esp_timer_get_time();
  capturing = true;
  delay(ms);
  capturing = false;
  uint32_t t1 = (uint32_t)esp_timer_get_time();
  Serial.printf("#CAP label=%s ms=%lu Y0=%u X0=%u edges=%lu overflow=%lu\n", label.c_str(),
                (unsigned long)ms, y0, x0, (unsigned long)nEdges, (unsigned long)overflow);
  emitChannel(0, y0, t0, t1);
  emitChannel(1, x0, t0, t1);
  Serial.println("#END");
}

static void help() {
  Serial.println("# c <label> [ms] : 記録 / m : ライブ表示切替 / ? : ヘルプ");
  Serial.printf("# CH Y=GPIO%u  CH X=GPIO%u\n", PIN_Y, PIN_X);
}

void setup() {
  Serial.begin(115200);
  edges = (Edge *)malloc(sizeof(Edge) * MAX_EDGES);
  pinMode(PIN_Y, INPUT);   // 外付け分圧があるので内部プルは使わない
  pinMode(PIN_X, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_Y), isrY, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_X), isrX, CHANGE);
  delay(300);
  Serial.println("#READY led_sig_rec");
  help();
}

static bool live = false;
static uint32_t lastLive = 0;

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.startsWith("c")) {
      String rest = line.substring(1);
      rest.trim();
      int sp = rest.indexOf(' ');
      String label = sp < 0 ? rest : rest.substring(0, sp);
      uint32_t ms = sp < 0 ? 1000 : rest.substring(sp + 1).toInt();
      if (label.length() == 0) label = "cap";
      capture(label, ms ? ms : 1000);
    } else if (line == "m") {
      live = !live;
      Serial.printf("# live %s\n", live ? "ON" : "OFF");
    } else if (line.length()) {
      help();
    }
  }
  if (live && millis() - lastLive >= 500) {
    lastLive = millis();
    uint32_t cy = liveCnt[0], cx = liveCnt[1];
    liveCnt[0] = liveCnt[1] = 0;
    Serial.printf("# Y=%u (%lu edges/0.5s)  X=%u (%lu edges/0.5s)\n", digitalRead(PIN_Y),
                  (unsigned long)cy, digitalRead(PIN_X), (unsigned long)cx);
  }
}
