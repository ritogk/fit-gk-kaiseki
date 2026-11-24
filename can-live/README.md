# can-live — ライブ F-CAN 演奏アプリ

Honda Fit GK5 の **F-CAN をリアルタイム受信**し、運転操作を音にする自己完結アプリ。
現状は **回転数 → 音程 / ステア角 → 左右パン＋音色** のリアルタイム演奏（Web Audio）。
K-Line アプリ（[../kline-app/](../kline-app/), ポート 8000/5173）とは**完全に独立**。ポートは **8100 / 5273**。

受信は **python-can**（バックエンドは Linux=`socketcan` / macOS=`gs_usb`）で、送信は行わない受信専用アプリ。

> **macOS の現状**: 受信バックエンドが `server/can_reader.py` で `socketcan` に固定されているため、**このままでは Mac で実 CAN を受けられない**（SocketCAN は Linux カーネル機能）。切り替えに必要な変更は約16行で、確定版パッチが [../docs/macos-can.md](../docs/macos-can.md) にある。実ハード無しの検証は `vbus_test.py` で今すぐできる（後述）。

## 構成

```
can-live/
├── server/                       # Python バックエンド（CAN→WS）
│   ├── main.py                   # FastAPI + /api/canlive/ws（イベント駆動プッシュ）
│   ├── can_reader.py             # 専用スレッドで python-can 受信 + cantools デコード
│   ├── signals.py                # デコード dict → フロント信号 + 派生値
│   └── config.py                 # チャンネル / 500k / ポート / レート上限
├── honda_fit_gk5_generated.dbc   # F-CAN DBC（実車校正で要所を書き直し済み）
├── calib.py                      # 校正ツール: 操作前後の差分で「動くバイト」を特定
├── explore.py                    # 走行中アナログ信号の自動探索（相関ランク）
├── vbus_test.py                  # 仮想バス検証（実ハード不要。Mac でそのまま動く）
├── web/                          # Vue 3 + Vite フロント（可視化 + Web Audio 演奏）
└── run.sh                        # start|stop|restart（Linux 専用。can0 up も面倒見る）
```

## アーキテクチャ / 低遅延設計

```
CAN ──(python-can, 専用スレッド)──> cantools decode ──> 最新値dict
                                                          │ dirty 通知(call_soon_threadsafe)
                                                          ▼
                                          FastAPI WebSocket（イベント駆動・最大250Hz）
                                                          │ JSON
                                                          ▼
                  ブラウザ：(a)Vue 描画(RPMゲージ/ステア)  /  (b)onFrame→Web Audio 発音
```

- **固定周期プッシュをしない**: 受信フレーム到着で即送信（`asyncio.Event`）、`MAX_PUSH_HZ` でコアレス。
- **TCP_NODELAY**: localhost 想定。asyncio が既定で有効化するため Nagle 由来の遅延は出ない。
- **ブロッキング受信はスレッド側**: `bus.recv()` はイベントループを塞がない。
- **音と描画を分離**: WS 受信時、描画用 reactive 更新とは別に `onFrame(cb)` で生信号を即時配布。
  音は描画ループを介さず `AudioParam.setTargetAtTime` で最短スケジュール。

## 演奏マッピング（`web/src/audio/synth.ts`）

- **回転数 → 音程**: 800〜7000rpm を A マイナーペンタトニック ~3 オクターブに量子化（音楽的に外れない）。
- **ステア角 → 左右パン ＋ ローパス開度**: 切る方向に音が移動、切れ角で明るくなる（ワウ的）。
- 音色: ノコギリ波 ＋ サブのサイン → ローパス → パン。

## セットアップ (macOS)

venv はリポジトリルート共有。Python 3.10+ 必須（`X | None` 記法を使うため。システムの 3.9 では import 時に落ちる）。

```bash
cd ..
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r can-live/requirements.txt   # python-can, cantools
uv pip install --python .venv/bin/python gs_usb pyusb                   # macOS の CAN バックエンド
brew install libusb
```

`web/dist` はビルド済みで FastAPI が `/` にマウントするため、**`npm install` も Vite も要らない**。
フロントを触るときだけ `cd web && npm install && npx vite --port 5273`。

## 起動

### 実ハード無しで動かす（Mac で今すぐ動く）

仮想バスで受信 → デコード → WS 配信の一連を検証する。コード変更もアダプタも不要。

```bash
../.venv/bin/python vbus_test.py
```

ISO-TP / UDS の往復と、DBC デコード（rpm / ステア角 / スロットル / 車速 / ブレーキ）の一致を確認して PASS / FAIL を出す。

### 実車から受ける（macOS）

現状は `server/can_reader.py:49` が `interface="socketcan"` 固定なので、**先に gs_usb へ切り替えるパッチを当てる**。差分は [../docs/macos-can.md](../docs/macos-can.md) の「必要なパッチ (確定版)」にある。要点は3ファイル:

- `server/config.py` — `CAN_INTERFACE` / `CAN_CHANNEL` / `CAN_BITRATE` を環境変数化
- `server/can_reader.py` — `interface=CAN_INTERFACE` にし、gs_usb のときだけ `index=0, bitrate=...` を渡す
- `calib.py:23` / `explore.py:25` — 同じ差し替え（校正・探索ツールを使う場合のみ）

アダプタの検出確認:

```bash
../.venv/bin/python -c "from gs_usb.gs_usb import GsUsb; print(GsUsb.scan())"
```

パッチ適用後の起動:

```bash
CAN_INTERFACE=gs_usb CAN_BITRATE=500000 ../.venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8100
```

ブラウザで `http://localhost:8100` → **「▶ 演奏開始」**（autoplay 制限のためクリック必須）。
あとは空ぶかしで音程、ハンドルで左右パン＆音色。

ビットレートは `ip link` ではなく**起動時に環境変数で渡す**のが SocketCAN との運用差。バスを変えるときはプロセスを立て直す。

> `./run.sh`（および `../run-canlive.sh`）は Linux 向け。`ensure_can0` が `ip link` を叩くので macOS では起動時点で落ちる。上の uvicorn 直起動を使う。

### Linux から受ける

```bash
sudo ip link set can0 up type can bitrate 500000
./run.sh start          # WS(8100) + Vite(5273)
./run.sh start --dev    # uvicorn を --reload で（開発時のみ）
./run.sh stop
```

パッチ適用後も Linux では `CAN_INTERFACE` を未指定（=`socketcan`）にすること。**Linux で gs_usb を選ぶと `start()` がカーネルドライバを detach して `can0` が消える。**

## 実車校正の記録（DBC は自動生成の推測値を実測で修正済み）

`honda_fit_gk5_generated.dbc` は元々 medium 信頼度の自動生成で ID/バイト割当が誤っていた。
`calib.py`（操作前後の差分）で実車計測し、以下を確定・修正した:

| 信号 | 実体（実測） | 備考 |
|---|---|---|
| アクセル | `0x130` B3（0〜100%） | ドライブバイワイヤのアナログ |
| 回転数 | `0x17C` B2-B3（16bit, アイドル≈664） | 旧DBCは「水温」と誤ラベル |
| ステア角 | `0x156` B0-B1（符号付16bit ×0.1） | 旧DBCは「車速」と誤ラベル（G/速度のバグ源） |
| 車速 | `0x1D0` 4輪速（前輪平均, km/h） | 走行解析で確定 |
| ブレーキ | `0x1A4` B0（0/1/2 状態） | アナログ踏力は F-CAN に無し（ON/OFF的） |
| クラッチ | 該当なし | F-CAN に信号が出ていない |

未確定: バッテリー電圧・ギア・水温の実位置・外気温（旧DBCの値は当てにならない）。
横G/ヨーは走行＋旋回データがあれば `explore.py` の相関で特定可能（未実施）。
