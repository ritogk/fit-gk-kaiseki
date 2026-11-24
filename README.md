# fit-gk-kaiseki

自分の Honda Fit GK5 RS MT を解析・制御して遊ぶモノレポ。 K-Line 診断の解析から始まり、 CAN ライブ受信、 マイコンによる直接電気駆動まで、 アプローチ別にサブプロジェクトを分けている。

自分の車両 + 私的環境での研究目的限定です。 公道で勝手に光らせたりホーンを鳴らしたりはしないでください。 Honda とも当然無関係。

## サブプロジェクト

| ディレクトリ | 内容 | 経路 |
|---|---|---|
| [kline-app/](kline-app/) | K-Line (ISO 14230) IO Control で灯火・ロック等を操作する FastAPI + Vue アプリ。Launchpad X ライブ演奏対応 | OBD2 K-Line 診断 |
| [can-live/](can-live/) | F-CAN ライブ受信 → RPM×ステアのリアルタイム演奏アプリ | CAN 受信 |
| [micro-control/](micro-control/) | ESP32-S3 + BTS7960 で灯火等を PWM 直接駆動するライブ制御システム (開発中) | 車両配線に直結 |

## 共通リソース

- [docs/findings.md](docs/findings.md) — K-Line 解析の全記録 (LID/IOCP マップ、行き止まり込み)
- [docs/macos-can.md](docs/macos-can.md) — macOS で CAN アダプタを動かす調査記録
- `docs/screenshots/` — UI スクリーンショット

## セットアップ

Python venv はリポジトリルートの `.venv` を kline-app / can-live で共有する。 **Python 3.10+ が必須** (コードが `X | None` 記法を使うため)。

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r kline-app/requirements.txt -r can-live/requirements.txt
```

macOS で CAN も使うなら追加で:

```bash
brew install libusb
uv pip install --python .venv/bin/python gs_usb pyusb
```

micro-control はファームウェア (Arduino IDE 2.x / arduino-cli) のため venv 不要。 書き込み手順は [micro-control/README.md](micro-control/README.md)。

## 起動 (macOS)

各サブプロジェクトの FastAPI がビルド済みフロント (`web/dist`) を `/` に配信するので、 **uvicorn 1本で UI まで出る**。 `npm install` も Vite も要らない。

```bash
# kline-app: K-Line 制御 UI → http://127.0.0.1:8000/
cd kline-app
KLINE_PORT=$(ls /dev/cu.usbserial-* | head -1) ../.venv/bin/uvicorn api.main:app --port 8000

# can-live: F-CAN ライブ受信 → http://127.0.0.1:8100/
#   ※ 実車受信には gs_usb への切り替えパッチが必要 (can-live/README.md 参照)
cd can-live
CAN_INTERFACE=gs_usb CAN_BITRATE=500000 ../.venv/bin/uvicorn server.main:app --port 8100
```

ルートの `run-*.sh` は **Linux 向け**。 `/dev/ttyUSB0` 固定・`ip link`・`npx vite` に依存しているため macOS では落ちる。

## 起動 (Linux)

```bash
./run-kline.sh      # kline-app: API (8000) + Web (5173)
./run-keyboard.sh   # kline-app: Launchpad キーボードブリッジ (Linux 専用)
./run-canlive.sh    # can-live: can0 を up → WS (8100) + Web (5273)
```

## OS ごとの対応状況

| | macOS (Apple Silicon) | Linux (Ubuntu/Debian) |
|---|---|---|
| kline-app (K-Line 制御) | **動作確認済み**。ポートは `/dev/cu.usbserial-*` | 動作確認済み。ポートは `/dev/ttyUSB0` |
| can-live (F-CAN 受信) | 要パッチ (`socketcan`→`gs_usb`, 約16行)。仮想バス検証は無改造で可 | **実車で受信確認済み** |
| Launchpad ブリッジ | 不可 (ALSA / `/dev/uinput` 依存) | 動作確認済み |
| CAN のツール類 | python-can 同梱 CLI (`can_viewer` / `can_logger` / `can_player`) | can-utils (`candump` / `cansend` / `canplayer`) |

## ライセンス

MIT。 [LICENSE](LICENSE) 参照。 自分の車で、 自分のリスクで遊んでください。
