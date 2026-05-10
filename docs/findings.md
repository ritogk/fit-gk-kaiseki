# Findings — Honda Fit GK5 K-Line ECM(0x10) IO Control

## ハードウェア

- 車両: Honda Fit GK5 RS MT (型式 GK5、 6MT)
- ケーブル: アリエクスプレス系の **FT232RL + L9637D** OBD2 USBケーブル (`USB ID 0403:6001`)。 ELM327エミュレータでは**ない**、 純粋なシリアル ↔ K-Line トランシーバ
- ホスト: Linux、 `/dev/ttyUSB0`、 10400 bps 8N1

## プロトコル概要

- ISO 14230 (KWP2000) 準拠 — Honda HOBD独自プロトコルではない
- メッセージ形式: `0x80 [target] [source] [length] [SID...] [cs]`
- 短縮形 `0x81-0xBF` も受付 (length は format byte 下位 6bit)
- `0xC1` (no-addr 形式) は不受
- K-Line は半二重 → 自分の TX バイトは RX エコーで返る (パース時除去要)

## 接続シーケンス

1. **Fast Init**: BREAK 25ms LOW → 25ms HIGH (idle)
2. **直後** (W2 < 25ms 以内) StartCommunication 送信
3. StartComm req: `81 46 F1 81 39` → 応答 `80 F1 46 03 C1 DA 8F E4`
4. keyByte1=0xDA, keyByte2=0x8F (ISO 14230-4 適合)
5. Source ID は 0xF0 / 0xF1 / 0xF2 どれでも応答
6. 以降 ECM(0x10) に直接 IO Control を投げてOK

## 重要な ECU アドレスマップ (gateway 0x46 越し)

| addr | 役割 | 状態 |
|---|---|---|
| **0x10** | **ECM (エンジン)** ← **IO Control 受付の本命** | RDLI/IO Control 受付、 制御コマンドはここ宛 |
| 0x46 | K-Line 入口ゲートウェイ (MICU 外面) | StartComm のみ応答、 他SID全 silent |
| 0x72 | MICU/BCM 本体 | RDLI で部品番号読取、 IO Control は全 NR general (認証要) |
| 0x75 | Security Access 必須 ECU | 詳細未解析 |

## 確定した IO Control LIDマップ (ECM 0x10)

`80 10 F0 08 30 [LID] [IOCP] 00 00 00 00 00 [cs]` (8byte payload + cs) で投げる。

### IOCP=0x0F (ON/Start — ライト系)

| LID | 機能 | Envelope |
|---|---|---|
| 0x08 | ハザード | 15s (ドア閉時 MICU即cancel) |
| 0x0A | 左ウィンカー | 5s |
| 0x0B | 右ウィンカー | 5s |
| 0x1C | ヘッドロー | 15s |
| 0x1D | ハイビーム | 15s |
| 0x20 | フォグランプ | 15s (ライトON状態でないと視認できない) |
| 0x25 | 車幅灯 | 15s |

### IOCP=0x01 (パルス — 即時系)

| LID | 機能 | Envelope |
|---|---|---|
| 0x04 | 全ロック | 即時1発 |
| 0x05 | 全解錠 | 即時1発 |
| 0x09 | トランク開放 | 即時1発 |
| 0x11 | ブザー/チャープ音 | 短 |
| 0x26 | ホーン | 1s |

## ★StopDiagSession による Envelope 短縮★

`80 10 F0 01 20 A1` (StopDiagSession) を IO Control 直後に投げると、 ECM が進行中の active test を強制中断する。 これでファクトリー固定 envelope を任意の長さに短縮可。

**手法**:

```
loop:
  while ON期間中:
    IOControl LID IOCP State送信
    1秒待機 (refresh間隔、 リレー駆動維持)
  StopDiagSession 送信 (強制OFF)
  OFF期間分待機
```

**ハイビーム高速点滅 検証結果**:

| ON / OFF | 周波数 | 視認 |
|---|---|---|
| 0.5s / 0.5s | 1Hz | 余裕 |
| 0.3s / 0.1s | 2.5Hz | OK |
| 0.2s / 0.1s | 3Hz | OK |
| 0.1s / 0.1s | 4.4Hz | OK |
| 0.05s / 0.05s | 7.9Hz | 連続気味 (ハロゲン熱慣性) |

→ transaction overhead ~50-70ms / cycle、 上限 ~8-10Hz が実用。 これより速くするには ON時間 0.05s 未満 → フィラメント加熱不足で見えにくい。

## 行き止まり報告: ワイパー / ウォッシャー

**結論**: K-Line / ECM(0x10) IO Control 経由で wiper 制御は **到達不可能**。

NRC=0x10 cluster (条件未達: `0x06, 0x07, 0x10, 0x17, 0x23, 0x24, 0x27, 0x31, 0x32, 0x36, 0x37, 0x3C`) に wiper LID が含まれてる可能性が高いが、 以下を全部潰してもゲートが解けない:

| 試行 | 結果 |
|---|---|
| LID 0x28-0x4F (IOCP=0x0F) | 全 NRC=0x31 (out of range) — ECM サポート LID は 0x00-0x27 まで |
| SID 0x10 session 探索 (sub-fn 0x80-0x9F + 0x01-0x07) | **0x83 のみ PR**、 中で NRC=0x10 不変 |
| SID 0x27 Security Access on ECM | 全 NRC=0x31 — ECM に security 概念なし |
| State byte 9パターン変動 | 全 NRC=0x10 不変 |
| 別ECUアドレス 0x11-0xF8 で LID 0x06 試射 | 全 silent (0x88 の謎 PR は parser の echo 誤検出) |
| IOCP=0x02, 0x03 × LID 0x00-0x27 | NRC=0x10 cluster は IOCP=0x02/0x03 でも全 NRC=0x10、 LID 0x11(chirp) は IOCP=0x02 でも PR (新発見) |
| 車両状態: IGN ON / Engine OFF | 全 NRC=0x10 |
| Engine ON / Brake | 全 NRC=0x10 |
| Engine ON + ワイパー実走 | 全 NRC=0x10 |
| Engine ON + ワイパー実走 + ウォッシャー噴射 | 全 NRC=0x10 |

→ NRC=0x10 cluster のゲートは **vehicle-state ではなく**、 純正 HDS が固有の preamble/auth を使ってる可能性大。 K-Line aftermarket ケーブル単独では到達不可。 残るルートは (a) HDS純正 sniff (b) 物理リレータップ (c) F-CAN UDS で MICU 探索。

## 関連 reference

- `research/wiper_scan.py` — LID範囲スキャン
- `research/session_probe.py` — SID 0x10 sub-function 探索
- `research/wiper_dig.py` — Security Access + State + 別アドレス 一括 probe
- `research/iocp23_scan.py` — IOCP=0x02/0x03 LID走査
- `research/wiper_recheck.py` — NRC=0x10 cluster 車両状態切替時の再投入用
