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

## 起動 (ルートから)

```bash
./run-kline.sh      # kline-app: API (8000) + Web (5173)
./run-keyboard.sh   # kline-app: Launchpad キーボードブリッジ
./run-canlive.sh    # can-live: WS サーバ (8100) + Web (5273)
```

Python venv はリポジトリルートの `.venv` を kline-app / can-live で共有:

```bash
python3 -m virtualenv .venv
.venv/bin/pip install -r kline-app/requirements.txt -r can-live/requirements.txt
```

micro-control はファームウェア (Arduino IDE 2.x) のため venv 不要。書き込み手順は [micro-control/README.md](micro-control/README.md)。

## ライセンス

MIT。 [LICENSE](LICENSE) 参照。 自分の車で、 自分のリスクで遊んでください。
