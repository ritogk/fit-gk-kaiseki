# fit-gk-kaiseki

Honda Fit GK5 (2014-2020) の K-Line / OBD2 解析プロジェクト。 ECM(0x10) IO Control 経由で MICU 配下のリレー (ハザード/ライト/ロック等) を駆動するためのライブラリ・ FastAPI・ Vue 3 フロントを含みます。

> ⚠ 自分の車両での研究・教育目的限定です。 公道や他人の車両での実行はやめてください。 Honda・関係企業とは一切無関係。

## できること

| 機能 | LID | IOCP | Envelope |
|---|---|---|---|
| ハザード | 0x08 | 0x0F | ~15s (ドア閉時 MICU即cancel) |
| 左ウィンカー | 0x0A | 0x0F | ~5s |
| 右ウィンカー | 0x0B | 0x0F | ~5s |
| ロービーム | 0x1C | 0x0F | ~15s |
| ハイビーム | 0x1D | 0x0F | ~15s |
| フォグ | 0x20 | 0x0F | ~15s |
| 車幅灯 | 0x25 | 0x0F | ~15s |
| 全ロック | 0x04 | 0x01 | パルス |
| 全解錠 | 0x05 | 0x01 | パルス |
| トランク開放 | 0x09 | 0x01 | パルス |
| ブザー/チャープ | 0x11 | 0x01 | 短 |
| ホーン | 0x26 | 0x01 | ~1s |

加えて **StopDiagSession (SID 0x20) で envelope を任意の長さに短縮可能**。 これを利用したビート/リズム演奏 (ハイビーム + ロービーム + ハザードで「4分音符 + 8分裏 + downbeat」 等) もパターンライブラリに同梱。

詳細は [docs/findings.md](docs/findings.md) を参照。

## ハードウェア

- Honda Fit GK5 RS MT (型式: GK5、 2014-2020 想定)
- アリエクスプレス系の **FT232RL + L9637D OBD2 USBケーブル** (ELM327エミュレータでは**ない** 純粋なシリアル↔K-Line ケーブル)
- Linux ホスト (本リポジトリは Ubuntu/Debian で動作確認)

## セットアップ

```bash
git clone https://github.com/<you>/fit-gk-kaiseki.git
cd fit-gk-kaiseki
python3 -m virtualenv .venv
.venv/bin/pip install -r requirements.txt
```

シリアルポート (デフォルト `/dev/ttyUSB0`) のパーミッションが必要です。 `dialout` グループ所属が無ければ:

```bash
sudo chmod 666 /dev/ttyUSB0   # USB抜き差し毎に必要
# または:
sudo usermod -aG dialout $USER && newgrp dialout
```

別のポートを使うには環境変数 `KLINE_PORT` を設定:

```bash
export KLINE_PORT=/dev/ttyUSB1
```

## 起動方法

### A) FastAPI + Vue UI

```bash
./run.sh
# → http://127.0.0.1:8000/        Vue 3 操作UI
# → http://127.0.0.1:8000/docs    Swagger
```

### B) CLI から直接

```bash
.venv/bin/python scripts/fire.py list
.venv/bin/python scripts/fire.py hazard 5
.venv/bin/python scripts/fire.py chirp
.venv/bin/python scripts/play.py 3way 120 8
.venv/bin/python scripts/play.py pattern 1D 0F 0.1 0.1 12   # ハイビーム 0.1s/0.1s × 12回
```

`research/` 以下の旧スクリプトも同じ K-Line ケーブルで動きます。 解析 (= 「kaiseki」) の過程 — 行き止まり報告含む — を残してあります。

## API 仕様

### 個別操作 (`/api/control`)

| メソッド | パス | 内容 |
|---|---|---|
| GET  | `/api/control/list` | 利用可能コマンド一覧 |
| POST | `/api/control/{name}?duration_s=N` | コマンド実行 |

`name` は `hazard / turn_left / turn_right / low_beam / high_beam / fog / position / lock / unlock / trunk / chirp / horn`。 `duration_s` 省略時は default envelope。

### 演奏系 (`/api/fun`)

| メソッド | パス | 内容 |
|---|---|---|
| POST | `/api/fun/3way?bpm=120&measures=8` | HB(4分) + LB(8分裏) + HZ(downbeat) |
| POST | `/api/fun/beat?bpm=120&measures=8` | HB+PS の4つ打ち |
| POST | `/api/fun/stereo?bpm=120&measures=8` | 左右ウィンカー stereo + HB |
| POST | `/api/fun/polyrhythm?bpm=120&measures=8` | 4-against-3 |
| POST | `/api/fun/pattern?lid=&iocp=&on_s=&off_s=&cycles=` | 任意LID自由パターン |
| POST | `/api/fun/stop` | 演奏中パターンを次の beat 前に強制停止 |
| GET  | `/api/fun/status` | 演奏状態 + 直前の結果 |

演奏は背景スレッド実行、 同時実行不可 (HTTP 409)。

## ディレクトリ構成

```
fit-gk-kaiseki/
├── kline/        K-Line client (ISO 14230 / KWP2000 抽象化)
│   ├── client.py    StartComm / IO Control / StopDiag
│   ├── commands.py  名前付き個別コマンド (hazard, lights, locks 等)
│   └── patterns.py  ビート/リズム演奏 + cancel フラグ
├── api/          FastAPI (control / fun ルーター)
├── web/          Vue 3 (CDN) + Tailwind (CDN) — single-file SPA
├── scripts/      CLI ラッパー (fire.py, play.py)
├── research/     解析過程の生スクリプト (公開用に path 抽象化済)
└── docs/findings.md  研究結果まとめ
```

## 既知の到達点と限界

- ✅ `IOCP=0x0F` (lights) と `IOCP=0x01` (pulse) 両系統を確認
- ✅ StopDiagSession による envelope 短縮テクニック確立 (~7-8Hz まで実用)
- ❌ **wiper / washer は到達不可** — NRC=0x10 cluster (LID 0x06,0x07,0x10,0x17,0x23,0x24,0x27,0x31,0x32,0x36,0x37,0x3C) は session 種別 / Security Access / IOCP 変動 / state byte / 別ECUアドレス / 全主要vehicle stateを試すも全部素通り。 純正 HDS が固有の preamble/auth を使ってる可能性大、 K-Line aftermarket ケーブル単独では限界。

詳細は [docs/findings.md](docs/findings.md)。

## ライセンス

MIT — [LICENSE](LICENSE) を参照。

## 免責

This project is independent research on the author's own vehicle and is not affiliated with, endorsed by, or sponsored by Honda Motor Co., Ltd. Any use is at the user's own risk; the author makes no warranties about safety, legality, or suitability for any purpose. Use only on a vehicle you own, in private property, with all reasonable safety precautions in place.
