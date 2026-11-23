// ハイビーム左右 ライブ調光 (HW-039 1枚, M+=右, M-=左)
// 入力2系統: USBシリアル(UART側, 115200) と Web画面(WiFi SoftAP + WebSocket)。後勝ちで反映し、状態を全Web画面へ通知する。
// 書き込み設定: USB CDC On Boot = Disabled (UART側でシリアルを使う)
//
// シリアルのコマンド(Enterで確定):
//   r<0-100>  右の明るさ(体感%, 小数可)  例: r12.5
//   l<0-100>  左の明るさ                  例: l30
//   b<0-100>  左右同時                    例: b50
//   t<ms>     フェード時間(0->100%)       例: t300
//   g<値>     ガンマ (LED=2.2 / ハロゲン=0.5 / 補正なし=1)  例: g2.2
//   f<Hz>     PWM周波数 (50-19000)        例: f200
//   0         全消灯
// シリアルの1キー操作(Enter不要):
//   u / j  右 +1 / -1     U / J  右 +5 / -5
//   i / k  左 +1 / -1     I / K  左 +5 / -5
//   スペース 全消灯       ?  状態表示
// 安全要件: 起動時EN=LOW・明るさ0%、全準備後にEN=HIGH、MAX_DUTY_PCTでcap

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>

// ---- 設定 ----
const char* AP_SSID = "FIT-LAMP";
const char* AP_PASS = "naa6ozrpy3";      // 8文字以上
const int PIN_RPWM = 4;   // 右 (M+)
const int PIN_LPWM = 6;   // 左 (M-)
const int PIN_EN   = 5;   // R_EN + L_EN
uint32_t pwmFreq = 1000;         // 起動時の値。LED想定。f<Hz> で変更できる(12bitの上限は約19.5kHz)
const uint8_t  PWM_RES  = 12;     // 0-4095
const float    MAX_DUTY_PCT = 100.0f;
float    gammaV = 2.2f;
uint32_t rampMs = 300;            // 減光は2倍速

struct Ch { int pin; float target; float cur; };
Ch ch[2] = { {PIN_RPWM, 0, 0}, {PIN_LPWM, 0, 0} };

WebServer http(80);
WebSocketsServer ws(81);
bool dirty = true;

const char PAGE[] PROGMEM = R"HTML(
<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ハイビーム調光</title>
<style>
:root{color-scheme:light;--bg:#f8f9fa;--fg:#212529;--card:#fff;--line:#dee2e6;--acc:#1971c2;--warn:#c92a2a}
body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,sans-serif}
main{max-width:640px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:4px 0 12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:12px}
.row{display:flex;align-items:center;gap:12px}
.name{width:3em;font-weight:600}
.val{width:4.5em;text-align:right;font-variant-numeric:tabular-nums;font-size:20px}
input[type=range]{flex:1;height:40px;accent-color:var(--acc)}
button{font-size:18px;padding:12px;border-radius:10px;border:1px solid var(--line);background:#fff}
#off{width:100%;background:var(--warn);color:#fff;border:none;font-weight:700}
.st{font-size:13px;color:#868e96;margin-top:8px}
.btns{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px}
</style></head><body><main>
<h1>ハイビーム調光</h1>
<div class="card">
 <div class="row"><span class="name">右</span><input id="r" type="range" min="0" max="100" step="0.1" value="0"><span class="val" id="rv">0.0</span></div>
 <div class="btns"><button data-k="r" data-d="-5">-5</button><button data-k="r" data-d="-1">-1</button><button data-k="r" data-d="1">+1</button><button data-k="r" data-d="5">+5</button></div>
</div>
<div class="card">
 <div class="row"><span class="name">左</span><input id="l" type="range" min="0" max="100" step="0.1" value="0"><span class="val" id="lv">0.0</span></div>
 <div class="btns"><button data-k="l" data-d="-5">-5</button><button data-k="l" data-d="-1">-1</button><button data-k="l" data-d="1">+1</button><button data-k="l" data-d="5">+5</button></div>
</div>
<div class="card">
 <div class="row"><span class="name">左右</span><input id="b" type="range" min="0" max="100" step="0.1" value="0"><span class="val" id="bv"></span></div>
 <div class="row" style="margin-top:8px"><span class="name">ﾌｪｰﾄﾞ</span><input id="t" type="range" min="0" max="3000" step="50" value="300"><span class="val" id="tv">300</span></div>
</div>
<button id="off">全消灯</button>
<div class="st" id="st">接続中…</div>
<script>
const $=id=>document.getElementById(id);let ws,drag={},pend={};
function conn(){ws=new WebSocket('ws://'+location.hostname+':81/');
 ws.onopen=()=>$('st').textContent='接続済み';
 ws.onclose=()=>{$('st').textContent='切断。再接続中…';setTimeout(conn,1000)};
 ws.onmessage=e=>{const p=e.data.split(' ');if(p[0]!=='S')return;
  const v={r:+p[1],l:+p[2],t:+p[3]};
  for(const k of ['r','l','t']){if(!drag[k])$(k).value=v[k];$(k+'v').textContent=k==='t'?v[k]:v[k].toFixed(1)}}}
function send(c){pend[c[0]]=c;requestAnimationFrame(flush)}
function flush(){if(ws&&ws.readyState===1)for(const k in pend)ws.send(pend[k]);pend={}}
for(const k of ['r','l','b','t']){const el=$(k);
 el.addEventListener('input',()=>{drag[k]=1;send(k+el.value);if(k!=='b')$(k+'v').textContent=k==='t'?el.value:(+el.value).toFixed(1)});
 el.addEventListener('change',()=>{drag[k]=0});
 el.addEventListener('pointerup',()=>{drag[k]=0})}
document.querySelectorAll('.btns button').forEach(b=>b.onclick=()=>{const k=b.dataset.k;
 const v=Math.max(0,Math.min(100,+$(k).value+ +b.dataset.d));$(k).value=v;send(k+v)});
$('off').onclick=()=>{$('b').value=0;send('0')};
conn();
</script></main></body></html>
)HTML";

uint32_t toDuty(float pct) {
  if (pct <= 0) return 0;
  float d = powf(pct / 100.0f, gammaV) * 4095.0f;
  float cap = 4095.0f * MAX_DUTY_PCT / 100.0f;
  if (d > cap) d = cap;
  return (uint32_t)(d + 0.5f);
}

void setTarget(int i, float v) { ch[i].target = constrain(v, 0.0f, 100.0f); dirty = true; }

void printState() {
  Serial.printf("R=%.1f%% L=%.1f%% fade=%ums gamma=%.2f freq=%uHz\n", ch[0].target, ch[1].target, rampMs, gammaV, pwmFreq);
}

// シリアルとWebで共通のコマンド処理
void handleCmd(String s) {
  s.trim();
  if (s.length() == 0) return;
  char c = s.charAt(0);
  float v = s.substring(1).toFloat();
  if (s == "0")      { setTarget(0, 0); setTarget(1, 0); }
  else if (c == 'r') setTarget(0, v);
  else if (c == 'l') setTarget(1, v);
  else if (c == 'b') { setTarget(0, v); setTarget(1, v); }
  else if (c == 't') { rampMs = constrain((int)v, 0, 10000); dirty = true; }
  else if (c == 'g') { if (v >= 0.3f && v <= 3.0f) gammaV = v; }
  else if (c == 'f') {
    uint32_t f = (uint32_t)v;
    if (f >= 50 && f <= 19000) {
      pwmFreq = f;
      for (auto &k : ch) ledcChangeFrequency(k.pin, pwmFreq, PWM_RES);
    }
  }
  else return;
}

bool hotkey(char c) {
  switch (c) {
    case 'u': setTarget(0, ch[0].target + 1); break;
    case 'j': setTarget(0, ch[0].target - 1); break;
    case 'U': setTarget(0, ch[0].target + 5); break;
    case 'J': setTarget(0, ch[0].target - 5); break;
    case 'i': setTarget(1, ch[1].target + 1); break;
    case 'k': setTarget(1, ch[1].target - 1); break;
    case 'I': setTarget(1, ch[1].target + 5); break;
    case 'K': setTarget(1, ch[1].target - 5); break;
    case ' ': setTarget(0, 0); setTarget(1, 0); break;
    case '?': break;
    default: return false;
  }
  printState();
  return true;
}

void onWs(uint8_t num, WStype_t type, uint8_t* payload, size_t len) {
  if (type == WStype_CONNECTED) dirty = true;
  else if (type == WStype_TEXT) handleCmd(String((char*)payload, len));
}

void setup() {
  pinMode(PIN_EN, OUTPUT);
  digitalWrite(PIN_EN, LOW);                     // 起動時の誤点灯防止
  pinMode(PIN_RPWM, OUTPUT); digitalWrite(PIN_RPWM, LOW);
  pinMode(PIN_LPWM, OUTPUT); digitalWrite(PIN_LPWM, LOW);

  Serial.begin(115200);
  ledcAttach(PIN_RPWM, pwmFreq, PWM_RES);
  ledcAttach(PIN_LPWM, pwmFreq, PWM_RES);
  ledcWrite(PIN_RPWM, 0);
  ledcWrite(PIN_LPWM, 0);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  WiFi.setSleep(false);                          // 応答遅延を減らす
  http.on("/", []() { http.send_P(200, "text/html; charset=utf-8", PAGE); });
  http.begin();
  ws.begin();
  ws.onEvent(onWs);

  digitalWrite(PIN_EN, HIGH);                    // 全準備完了後に出力許可
  Serial.printf("hibeam_live ready. WiFi:%s  http://%s/\n", AP_SSID, WiFi.softAPIP().toString().c_str());
  printState();
}

void loop() {
  static String buf;
  while (Serial.available()) {
    char c = Serial.read();
    if (buf.length() == 0 && hotkey(c)) continue;
    if (c == '\n' || c == '\r') { if (buf.length()) { handleCmd(buf); printState(); } buf = ""; }
    else buf += c;
  }
  http.handleClient();
  ws.loop();

  static uint32_t last = millis();
  uint32_t now = millis();
  float dt = (float)(now - last);
  last = now;
  for (auto &k : ch) {
    float step = (rampMs == 0) ? 100.0f : 100.0f * dt / rampMs;
    if (k.cur < k.target)      k.cur = min(k.target, k.cur + step);
    else if (k.cur > k.target) k.cur = max(k.target, k.cur - step * 2);
    ledcWrite(k.pin, toDuty(k.cur));
  }

  static uint32_t lastTx = 0;
  if (dirty && now - lastTx >= 30) {             // 通知は最短30ms間隔
    char m[48];
    snprintf(m, sizeof(m), "S %.1f %.1f %u", ch[0].target, ch[1].target, rampMs);
    ws.broadcastTXT(m);
    dirty = false; lastTx = now;
  }
  delay(1);
}
