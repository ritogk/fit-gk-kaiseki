# can-live — ライブ F-CAN 演奏アプリ

Honda Fit GK5 の **F-CAN を can0 からリアルタイム受信**し、運転操作を音にする自己完結アプリ。
現状は **回転数 → 音程 / ステア角 → 左右パン＋音色** のリアルタイム演奏（Web Audio）。
既存の K-Line アプリ（`../api` `../web`, ポート 8000/5173）とは**完全に独立**。ポートは **8100 / 5273**。

## 構成

```
can-live/
├── server/                       # Python バックエンド（can0→WS）
│   ├── main.py                   # FastAPI + /api/canlive/ws（イベント駆動プッシュ）
│   ├── can_reader.py             # 専用スレッドで socketcan 受信 + cantools デコード
│   ├── signals.py                # デコード dict → フロント信号 + 派生値
│   └── config.py                 # can0 / 500k / ポート / レート上限
├── honda_fit_gk5_generated.dbc   # F-CAN DBC（実車校正で要所を書き直し済み）
├── calib.py                      # 校正ツール: 操作前後の差分で「動くバイト」を特定
├── explore.py                    # 走行中アナログ信号の自動探索（相関ランク）
├── web/                          # Vue 3 + Vite フロント（可視化 + Web Audio 演奏）
└── run.sh                        # start|stop|restart（can0 up も面倒見る）
```

## アーキテクチャ / 低遅延設計

```
can0 ──(socketcan, 専用スレッド)──> cantools decode ──> 最新値dict
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

## セットアップ

```bash
../.venv/bin/pip install -r requirements.txt   # python-can, cantools
cd web && npm install && cd ..
```

## 起動

```bash
# リポジトリ root から
./run-canlive.sh start          # can0 を up → WS(8100) + Vite(5273)
./run-canlive.sh start --dev    # uvicorn を --reload で（開発時のみ）
./run-canlive.sh stop
```

ブラウザで `http://localhost:5273` → **「▶ 演奏開始」**（autoplay 制限のためクリック必須）。
あとは空ぶかしで音程、ハンドルで左右パン＆音色。

CAN-USB アダプタ（gs_usb / candleLight, `can0`）を接続しておくこと。`run.sh` が未 up なら
`sudo ip link set can0 up type can bitrate 500000` を実行する（sudo パスワードを聞かれる）。

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
