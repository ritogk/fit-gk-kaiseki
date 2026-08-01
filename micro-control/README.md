# micro-control — ESP32-S3 車両直接制御

> [fit-gk-kaiseki](../README.md) のサブプロジェクト。

診断プロトコル (K-Line/CAN) を介さず、 ESP32-S3 + BTS7960 で車両の灯火等を PWM 直接駆動するライブ制御システム。 MIDI コントローラーで実車を「演奏」する。 現在 CH1 (フォグ) の調光が実車動作確認済み。

仕様・安全要件・ロードマップの正本は [CLAUDE.md](CLAUDE.md)。

## 構成

```
CLAUDE.md    仕様の正本 (ハード構成 / ピンアサイン / 安全要件 / ロードマップ)
firmware/    Arduino スケッチ (1スケッチ = 1フォルダ)
  fog_controller_simple/   シリアルキー3段階。実車動作確認済み
  fog_controller_dimmer/   細かい調光版 (w/s/e/d + 数字直接指定)
  micro_control/           統合ファームウェア (これから開発)
hardware/    結線・ピンアサインのドキュメント
  pinout.md   ピンアサイン表 (変更禁止)
  wiring.md   電源系統・BTS7960 結線・GND 設計原則
```

`fog_controller_web` / `fog_controller_revD` は配布済みだが未収蔵。入手次第 `firmware/` に追加する。

## ビルド・書き込み

ターミナルから `build.sh` (arduino-cli ラッパー) で完結する。Arduino IDE 2.x でも同じ設定で開ける（ツールチェーン共有）。

```bash
./build.sh compile fog_controller_dimmer          # コンパイルのみ
./build.sh upload  fog_controller_dimmer          # コンパイル + 書き込み (ポート自動検出)
./build.sh flash   fog_controller_dimmer          # 書き込み + モニタ
./build.sh monitor                                # シリアルモニタ (115200)。dimmer のキー操作もここから
./build.sh ports                                  # 候補ポート一覧
```

- 前提: `brew install arduino-cli` + `arduino-cli core install esp32:esp32` (導入済み)
- ボード設定は build.sh 内で固定: ESP32S3 Dev Module / **USB CDC On Boot: Enabled** / FlashSize=8M / PSRAM=opi
- MIDI ファーム (USB Host) は `MIDI=1 ./build.sh ...` で USB-OTG モードに切替 + ライブラリ `ESP32_Host_MIDI`
- ポート: `/dev/cu.usbmodem*` (ネイティブUSB) / `/dev/cu.wchusbserial*` (UART側 CH343)
- USB Host モード時は OTG ポートがシリアルにならないため、書き込み/モニタは UART 側 (CH343) を使う

## 安全上の注意

- BTS7960 の **RPWM/LPWM 同時 HIGH は貫通短絡で破損** (絶対禁止)
- `setup()` 冒頭で EN ピンを LOW 初期化、起動時輝度 0% (誤点灯防止)
- 詳細は [CLAUDE.md](CLAUDE.md) の安全要件を参照 (削除禁止)
