# macOS で CAN を動かす — 調査記録 (2026-07-28)

Mac (Apple Silicon / Darwin 25.4) で `can-live` を動かせるか調べた記録。 **実アダプタを繋いだ実測は未実施**（次回）。 ここに書いてあるのは仮想バス・ライブラリ検証・ソース確認までで確定した内容。

## 結論

- **動く。** SocketCAN を捨てて python-can の `gs_usb` バックエンドに切り替えるだけ。 Linux VM も別ハードも要らない。
- 必要な変更は `server/config.py` +7行 / `server/can_reader.py` +9行 の計16行。 パッチ内容は下記に確定版を置いてある。
- **送信もできる。** ISO-TP マルチフレーム + UDS 往復まで純Pythonで通ることを実測済み。 Linux の `can-isotp.ko` は不要。
- 前提条件が1つ: **Python 3.10 以上が必須**。 Mac のシステム Python は 3.9.6 で、 `CanReader | None` 等の注記が import 時に `TypeError` になる。

## なぜ現状動かないか (実測)

| 項目 | 結果 |
|---|---|
| `can.interface.Bus(interface="socketcan")` | `OSError [Errno 43] Protocol not supported` — macOS カーネルに SocketCAN が無い |
| `ip` / `candump` / `cansend` / `slcand` | 全て未インストール。 `can-live/run.sh` の `ensure_can0` が `ip link` 実行時点で落ちる |
| 無改造で起動した場合 | サーバと WS は正常に立つ。 `alive=false` / `rpm=0` / 観測フレーム0 のまま1秒ごと再接続を試み続ける。 クラッシュはしない |
| システム Python 3.9.6 で import | `TypeError: unsupported operand type(s) for \|` |

## gs_usb バックエンド (本命)

python-can の `gs_usb` は **Windows / Linux / Mac 対応**が公式ドキュメントに明記されており、 対象デバイスとして candleLight / CANable / CANtact が名指しされている。 手持ちのアダプタ (`1d50:606f`) はまさにこれ。 SocketCAN のカーネルドライバではなく **libusb 経由のユーザ空間実装**なので macOS でもそのまま動く。

Mac 上で到達点を実測した結果:

| 確認項目 | 結果 |
|---|---|
| libusb | Homebrew で 1.0.30 導入済み |
| pyusb バックエンド取得 | OK (`ctypes.util.find_library` は None を返すが pyusb 1.3.1 の fallback が拾う) |
| USB デバイス列挙 | OK (11台列挙。 ただし CAN アダプタは未接続だった) |
| `GsUsb.scan()` | 実行可能、 0台を返す |
| `can.Bus(interface="gs_usb", index=0, bitrate=500000)` | `CanInitializationError: Cannot find device 0. Devices found: 0` |

最後の行が重要で、 **アダプタ未接続という理由だけで止まっている**。 macOS 固有の障壁（権限 / kext / ドライバ署名）は一つも踏んでいない。 Windows で必要な Zadig 相当の作業も macOS では不要。

例外型が `CanError` 系なので、 既存の `except (OSError, can.CanError)` の1秒リトライループにそのまま収まる（実測でアダプタ待ちになることを確認）。

### 制約

- **ビットレートは Bus 生成時に渡す**。 SocketCAN の `ip link set can0 up type can bitrate ...` に相当する事前セットアップが gs_usb には無い。
- 対応レートは 10K / 20K / 50K / 83.333K / 100K / 125K / 250K / 500K / 800K / 1M の離散値のみ。 F-CAN の 500k、 B-CAN 想定の 125k はどちらも含まれる。
- メッセージフィルタ非対応。 can-live は全ID受けるので影響なし。
- `receive_own_messages=False` はそのまま渡してよい。 `BusABC.__init__` が `**kwargs: object` で余分を無視する。

## 必要なパッチ (確定版)

複製に当てて動作確認済み。 リポジトリ本体には未適用。

### `can-live/server/config.py`

```diff
+import os
 import pathlib

-CAN_CHANNEL = "can0"
-CAN_BITRATE = 500000
+# バックエンドを環境変数で切替（Linux=socketcan / macOS=gs_usb / 開発=virtual）。
+CAN_INTERFACE = os.environ.get("CAN_INTERFACE", "socketcan")
+CAN_CHANNEL = os.environ.get("CAN_CHANNEL", "can0")
+CAN_BITRATE = int(os.environ.get("CAN_BITRATE", "500000"))
```

### `can-live/server/can_reader.py`

```diff
-from .config import CAN_CHANNEL, DBC_PATH, STALE_SEC
+from .config import CAN_BITRATE, CAN_CHANNEL, CAN_INTERFACE, DBC_PATH, STALE_SEC
@@
+                kw = {}
+                if CAN_INTERFACE == "gs_usb":
+                    # gs_usb は起動時にビットレートを渡す（Linux の ip link 相当）
+                    kw = {"index": 0, "bitrate": CAN_BITRATE}
                 bus = can.interface.Bus(
                     channel=self._channel,
-                    interface="socketcan",
+                    interface=CAN_INTERFACE,
                     receive_own_messages=False,
+                    **kw,
                 )
```

### 同じ修正が要る箇所

- `can-live/calib.py:23` — `interface="socketcan"`
- `can-live/explore.py:25` — 同上

### `can-live/run.sh`

macOS では `ensure_can0`（`ip link`）を通ってはいけない。 OS 判定でスキップするか、 Mac では `run.sh` を使わず uvicorn / vite を直接叩く。

## 次回の手順

**`.venv` は 2026-07-28 時点で構築済み**（Python 3.12 / 依存導入済み / `vbus_test.py` PASS 確認済み）。 作り直す必要はない。 参考までに構築コマンド:

```bash
uv venv --python 3.12 .venv          # システムの 3.9 では動かないので必須
uv pip install --python .venv/bin/python -r requirements.txt -r can-live/requirements.txt \
    gs_usb pyusb can-isotp udsoncan websockets
```

再開時の手順:

```bash
# 1. アダプタを挿して検出確認（ここが今回できなかった唯一の点）
.venv/bin/python -c "from gs_usb.gs_usb import GsUsb; print(GsUsb.scan())"

# 2. 上記パッチを config.py / can_reader.py に適用（未適用のまま置いてある）

# 3. 起動
cd can-live && CAN_INTERFACE=gs_usb CAN_BITRATE=500000 ../.venv/bin/uvicorn server.main:app --port 8100
```

`candump` 等の代替は python-can 同梱 CLI で足りる: `can_logger` / `can_viewer` / `can_player` / `can_bridge`（それぞれ candump / candump の色付き表示 / canplayer / cangw 相当）。 Mac でそのまま動く。

## 送信 (CAN send) について

**Mac から送信できる。**

- `send()` は `BusABC` 共通APIで、 `can/interfaces/gs_usb.py` に実装が存在することをソースで確認済み。 バックエンドが何であれ呼び出し側のコードは同じ。
- **ISO-TP / UDS も通る。** Linux のカーネルモジュール `can-isotp.ko` は不要で、 `can-isotp` パッケージの純Python実装が python-can の任意バックエンドの上に載る。 仮想バス上でテスター役とECU役を立て、 12byte リクエスト（FirstFrame + FlowControl + ConsecutiveFrame のマルチフレーム）→ 40byte 肯定応答 の往復を実測 PASS。
- したがって README の「ミラー/PW は CAN インターフェースが要る」領域は **Mac + gs_usb + can-isotp + udsoncan** で狙える。 ただし現状リポジトリに `bus.send` は1箇所も無く、 can-live は受信専用。 送信側は完全に新規実装になる。
- 順序としては、 実車への書き込みになるので **先に受信で B-CAN のビットレートを確定**（README では 125k が未確定扱い）させてから。

## OS ごとの使い分け (Ubuntu + macOS 運用)

対象を Ubuntu と macOS の2つに絞る場合、 **同一ソース + `CAN_INTERFACE` の値の違いだけ**で回る。

| | Ubuntu | macOS |
|---|---|---|
| バックエンド | `socketcan` (現状のまま) | `gs_usb` |
| 事前準備 | `sudo ip link set can0 up type can bitrate 500000` | 不要（ビットレートは Bus 生成時に渡す） |
| 実績 | **実車で受信確認済み** (README の F-CAN 500k) | 未検証 |
| 共通 | `server/` `honda_fit_gk5_generated.dbc` `signals.py` `web/` ISO-TP/UDS層 python-can同梱CLI | 同左 |

**注意: Ubuntu で `gs_usb` バックエンドを使ってはいけない。** `gs_usb` パッケージの `start()` は非Windows環境でカーネルドライバを **detach する**（`gs_usb/gs_usb.py:56-59`）。 Linux で呼ぶと SocketCAN 側の `can0` が消え、 candump 等と共存できなくなる。 Ubuntu=socketcan / macOS=gs_usb と固定するのが正しい。 env 変数で分ける設計はこのためにも要る。

### 明日ハマるとしたらここ (未検証)

同じ `start()` の中で `is_kernel_driver_active(0)` を **try/except 無しで呼んでいる**。 libusb はこの機能を未対応プラットフォームで `LIBUSB_ERROR_NOT_SUPPORTED` として返し、 pyusb はそれを `NotImplementedError` に変換する（`usb/backend/libusb1.py:599-600, 918-920`）。 macOS の libusb がこれを実装していない場合、 アダプタを挿しても `bus.start()` の時点で落ちる。

python-can が公式に Mac 対応を明記している以上、 実際には通る公算が高い。 検証しようとしたが USB ドックが外れてデバイス数が 0 になり確認できなかった。 **もし `NotImplementedError` で落ちたら**、 原因はここなので `gs_usb/gs_usb.py` の当該2行を try/except で包めば回避できる。

## Linux が本当に要る部分 (境界)

「CAN をちゃんとやるなら Linux」という印象は**半分正しい**。 正しいのは *SocketCAN というカーネル機能とその周辺ツールが Linux 限定* という点で、 *生の read/write ができない* という意味ではない。 python-can が libusb 経由の実装を持っているので、 送受信そのものは移植されている。

| 機能 | macOS (gs_usb) | Linux (SocketCAN) |
|---|---|---|
| 生CANの受信 / 送信 | **可** | 可 |
| ISO-TP (マルチフレーム) | **可**。 `can-isotp` の純Python実装 | 可。 カーネル `can-isotp.ko` も選べる |
| UDS (`udsoncan`) | **可**。 下が ISO-TP なので同じ | 可 |
| 周期送信の精度 | Pythonスレッド実装。 10ms周期で実測 **σ=0.69ms / 最大ずれ 2.5ms** | カーネル BCM がタイマを打つのでPython の遅延と無関係 |
| 受信バッファリング | USB/libusb 依存。 Python 側が詰まると溢れる | カーネルがキューイング。 多少詰まっても落ちない |
| ハードウェアフィルタ | 非対応（全フレームが Python に来る） | カーネルフィルタあり |
| `candump` / `cansend` / `cangw` / `canplayer` | 使えない。 python-can 同梱の `can_logger` / `can_viewer` / `can_player` / `can_bridge` で代替 | 本家 can-utils |
| `vcan` (仮想インターフェース) | 使えない。 python-can の `virtual` バスで代替（同一プロセス内限定） | あり |
| タイムスタンプ | ユーザ空間 | カーネルタイムスタンプ |

実務上効いてくるのは**周期送信**と**受信バッファ**の2つ。

- 周期送信: python-can の `send_periodic()` は、 socketcan バックエンドならカーネル BCM に投げるが、 gs_usb には独自実装が無く `ThreadBasedCyclicSendTask`（Pythonスレッド）にフォールバックする。 実測では 10ms 周期で平均 10.00ms・標準偏差 0.69ms・最大ずれ 2.5ms。 B-CAN に周期フレームを流し込む用途なら許容できる公算が高いが、 厳密な周期を要求する ECU 相手だと Linux が無難。
- 受信バッファ: SocketCAN はカーネルがキューを持つが、 gs_usb は 1フレーム = 1回の同期バルク転送で、 溢れの吸収はデバイス側 FIFO 頼み。 ただし Python 側の処理速度は 80万frame/s 出ているので（下記「性能」）、 実負荷 数千frame/s に対しては余裕がある。

結論としては、 **read も send も macOS で可能。 Linux が要るのは「can-utils を使いたい」「カーネル精度の周期送信が要る」「取りこぼしを絶対に許容できない」場合**。

## 代替手段 (gs_usb が実機で駄目だった場合)

| 手段 | 内容 | 評価 |
|---|---|---|
| slcan | アダプタを slcan ファームに焼き直すと `/dev/cu.usbmodem*` の普通のシリアルとして見え、 libusb すら不要 | ASCII プロトコル分のオーバーヘッドがあり gs_usb より遅い。 保険 |
| socketcand | Linux機(Pi等)にアダプタを挿してデーモンを立て、 Mac から TCP 越しに読む | 結局 Linux機が要る。 それならアプリごと Pi に置く方が素直 |
| Linux VM (UTM等) | USB passthrough で SocketCAN をそのまま使う。 コード無改造 | passthrough は QEMU バックエンド限定、 Apple Virtualization では不可、 Rosetta と排他。 安定性にも難ありとの報告。 遠回り |
| 仮想バス + ログ再生 | 車なしで UI / 演奏ロジックを開発 | `can_player` + `virtual` バス。 `CAN_INTERFACE=virtual` で今すぐ使える |

## 性能

Python 側はボトルネックにならない（実測、 Mac 上）:

| 対象 | スループット |
|---|---|
| cantools デコード単体 | 1,150,000 frame/s (0.9us/frame) |
| CanReader 相当ループ (生バイト記録・ロック込み) | 826,000 frame/s (1.2us/frame) |
| WS ペイロード生成 (signals + raw + frames) | 29,700 回/s (0.03ms/回) |

F-CAN 500k の実負荷は数千 frame/s なので2桁以上の余裕がある。

**唯一の未知数は USB 層**。 `gs_usb.read()` は 1フレームにつき1回の同期バルク転送を行う実装（`gs_usb/gs_usb.py:166`）で、 カーネル側でバッファリングする Linux の SocketCAN よりオーバーヘッドが大きい。 取りこぼしの有無は実機で要測定。 判定には `alive` と全ID分のフレームカウンタ（既に `raw_frames_snapshot()` が保持）を見ればよい。

## 検証済み: パイプライン本体 (仮想バス)

`can-live/vbus_test.py` を実行すると、 実ハード無しで受信→デコード→WS配信を確認できる。 今回の実測結果:

| 投入 | 期待 | 実測 |
|---|---|---|
| `0x17C` B2-B3 = 3500 | rpm 3500 | 3500 |
| `0x156` B0-B1 = -1234 | steeringAngle -123.4 | -123.4 |
| `0x130` B3 = 128 | throttle 50.2% | 50.2 |
| `0x1D0` 前輪 = 6000/6010 | speed 60.05km/h | 60.05 |
| `0x1A4` B0 = 1 | brakePressed true | true |

DBC 未定義ID (`0x999`) が生バイト一覧に出ること、 `alive` 判定、 バス断時の再接続、 Vite の `/api`→8100 プロキシ (WS対応込み) も併せて確認済み。 DBC・デコード・派生値・配信まわりに問題は無い。

## 未検証 (次回やること)

- 実アダプタを挿した `GsUsb.scan()` の検出。 今回は未接続だった。
- 実車 F-CAN 500k での gs_usb 受信の取りこぼし有無（USB層のスループット）。
- B-CAN 125k での受信可否。 README では未確定扱いのまま。
- 送信の実車投入。 仮想バスでのプロトコル検証までしか終わっていない。

## reference

- [python-can: Geschwister Schneider and candleLight](https://python-can.readthedocs.io/en/stable/interfaces/gs_usb.html)
- [python-can: CAN over Serial / SLCAN](https://python-can.readthedocs.io/en/stable/interfaces/slcan.html)
- [CANable — An Open-Source USB to CAN Adapter](https://canable.io/) / [Getting Started (ファーム切替)](https://canable.io/getting-started.html)
