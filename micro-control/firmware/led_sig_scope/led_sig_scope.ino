// led_sig_scope — 2系統の電圧波形を記録する簡易オシロ (ESP32-S3, ADC連続変換)
//
// 車の信号線2本の「電圧」と「時間変化」を同時に記録して Mac へ送る。
// 解析は tools/ledsig.py scope <label> [ms]。
//
// ── 配線(1系統あたり抵抗2本。A・Bとも同じ) ──────────
//   測りたい線 ──[100kΩ]──┬── GPIO1  (CH A) / GPIO2 (CH B)
//                          └─[22kΩ]── GND
//   車のGND ─────────────────── ESP32 GND
//   12V→2.16V、14.5V→2.61V、5V→0.90V になる(倍率 5.545)。
//   上が100kΩなので、12Vが直接来てもGPIOへ流れる電流は0.1mA程度で壊れない。
//   別の抵抗を使うときは「下÷(上+下)」が0.17〜0.22になる組にし、
//   Mac側で LEDSIG_DIV=(上+下)÷下 を指定する。
// ──────────────────────────────────────────────────
// 性能: 1系統あたり約40kHz(25µs刻み)。PWM(〜数kHz)と一定電圧は正確に見える。
//       9600bps以上の通信は「通信らしい」ことまでしか分からない(ロジアナの領分)。
//
// シリアル 921600bps。コマンド: s <label> [ms]  (既定200ms、最大1000ms)
// 出力: #SCOPE label=.. n=<1系統の点数> us=<実測の記録時間> → A/B 行(mVの3桁16進) → #END

#include <Arduino.h>
#include "esp_adc/adc_continuous.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"

static const adc_channel_t CH_A = ADC_CHANNEL_0;  // GPIO1
static const adc_channel_t CH_B = ADC_CHANNEL_1;  // GPIO2
static const uint32_t FS_TOTAL = 80000;           // 2系統合計。S3の上限は約83kHz
static const uint32_t MAX_N = 40000;              // 1系統あたり最大点数(1000ms)

static adc_continuous_handle_t adc;
static adc_cali_handle_t cali;
static uint16_t *bufA, *bufB;

static void adcInit() {
  adc_continuous_handle_cfg_t hc = {};
  hc.max_store_buf_size = 16384;
  hc.conv_frame_size = 1024;
  ESP_ERROR_CHECK(adc_continuous_new_handle(&hc, &adc));
  static adc_digi_pattern_config_t pat[2];
  adc_channel_t chs[2] = {CH_A, CH_B};
  for (int i = 0; i < 2; i++) {
    pat[i].atten = ADC_ATTEN_DB_12;
    pat[i].channel = chs[i];
    pat[i].unit = ADC_UNIT_1;
    pat[i].bit_width = ADC_BITWIDTH_12;
  }
  adc_continuous_config_t cc = {};
  cc.pattern_num = 2;
  cc.adc_pattern = pat;
  cc.sample_freq_hz = FS_TOTAL;
  cc.conv_mode = ADC_CONV_SINGLE_UNIT_1;
  cc.format = ADC_DIGI_OUTPUT_FORMAT_TYPE2;
  ESP_ERROR_CHECK(adc_continuous_config(adc, &cc));
  adc_cali_curve_fitting_config_t cal = {};
  cal.unit_id = ADC_UNIT_1;
  cal.atten = ADC_ATTEN_DB_12;
  cal.bitwidth = ADC_BITWIDTH_12;
  if (adc_cali_create_scheme_curve_fitting(&cal, &cali) != ESP_OK) cali = NULL;
}

static void dump(char name, uint16_t *b, uint32_t n) {
  for (uint32_t i = 0; i < n; i++) {
    if (i % 64 == 0) Serial.printf("%s%c ", i ? "\n" : "", name);
    int mv = b[i] * 3100 / 4095;  // 校正が使えないときの概算
    if (cali) adc_cali_raw_to_voltage(cali, b[i], &mv);
    Serial.printf("%03x", constrain(mv, 0, 4095));
  }
  Serial.println();
}

static void capture(const String &label, uint32_t ms) {
  ms = constrain(ms, 10UL, 1000UL);
  uint32_t want = FS_TOTAL / 2 * ms / 1000, na = 0, nb = 0;
  static uint8_t raw[1024];
  uint32_t got;
  ESP_ERROR_CHECK(adc_continuous_start(adc));
  for (int i = 0; i < 4; i++) adc_continuous_read(adc, raw, sizeof(raw), &got, 100);  // 立ち上がり分を捨てる
  int64_t t0 = esp_timer_get_time();
  while (na < want || nb < want) {
    if (adc_continuous_read(adc, raw, sizeof(raw), &got, 200) != ESP_OK) break;
    for (uint32_t i = 0; i + 3 < got; i += SOC_ADC_DIGI_RESULT_BYTES) {
      adc_digi_output_data_t *p = (adc_digi_output_data_t *)&raw[i];
      if (p->type2.channel == CH_A && na < want) bufA[na++] = p->type2.data;
      else if (p->type2.channel == CH_B && nb < want) bufB[nb++] = p->type2.data;
    }
  }
  int64_t t1 = esp_timer_get_time();
  adc_continuous_stop(adc);
  uint32_t n = min(na, nb);
  Serial.printf("#SCOPE label=%s n=%lu us=%lld\n", label.c_str(), (unsigned long)n, t1 - t0);
  dump('A', bufA, n);
  dump('B', bufB, n);
  Serial.println("#END");
}

void setup() {
  Serial.begin(921600);
  bufA = (uint16_t *)malloc(MAX_N * 2);
  bufB = (uint16_t *)malloc(MAX_N * 2);
  adcInit();
  delay(300);
  Serial.println("#READY led_sig_scope  s <label> [ms]  A=GPIO1 B=GPIO2");
}

void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.startsWith("s")) {
    String rest = line.substring(1);
    rest.trim();
    int sp = rest.indexOf(' ');
    String label = sp < 0 ? rest : rest.substring(0, sp);
    uint32_t ms = sp < 0 ? 200 : rest.substring(sp + 1).toInt();
    capture(label.length() ? label : String("cap"), ms ? ms : 200);
  } else if (line.length()) {
    Serial.println("# s <label> [ms]");
  }
}
