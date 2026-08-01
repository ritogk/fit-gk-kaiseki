# ピンアサイン (変更禁止)

Freenove ESP32-S3 Board Lite (FNK0099) ↔ BTS7960 (IBT-2)。 変更する場合は必ず CLAUDE.md と同時に更新すること。

| ESP32 | 接続先 | 役割 |
|---|---|---|
| GPIO4 | BTS7960 RPWM | PWM出力(明るさ) |
| GPIO5 | BTS7960 R_EN + L_EN(束ね) | 出力許可。**起動時LOW必須** |
| GPIO2 | BTS7960 R_IS(配線のみ、未実装) | 電流センス(将来の球切れ検知用) |
| 3V3 | BTS7960 VCC | ロジック電源 |
| GND | BTS7960 GND → GNDバスバー | 一点集約 |
| GPIO6/7/8 | (予約) | 将来のCH2(ヘッドライト)/CH3・4(ウィンカー) |
| GPIO9 | (予約) | 将来の系統切替リレー駆動 |

## BTS7960 側の固定結線

- LPWM → GND 固定
- L_IS → 開放
- **RPWM/LPWM 同時 HIGH は貫通短絡で破損 (絶対禁止)**

## USB ポート (ESP32-S3 Board Lite は USB-C ×2)

| ポート | チップ | 用途 |
|---|---|---|
| UART側 | CH343 | 書き込み / シリアルモニタ |
| OTG側 | ネイティブUSB | MIDI 機器接続 (USB Host モード時) |
