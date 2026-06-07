"""can-live FastAPI エントリ。

- can0 をライブ受信（CanReader, 専用スレッド）
- /api/canlive/ws で WebSocket 配信（イベント駆動・低遅延）
- web/dist を / に静的配信

低遅延設計:
- 固定周期プッシュはしない。受信スレッドが新フレーム反映後に asyncio.Event(dirty)
  を立て、送信タスクは ``await dirty.wait()`` で即起床→送信。MAX_PUSH_HZ でコアレス。
- Nagle: asyncio は create_server のソケットに TCP_NODELAY をデフォルトで有効化するため、
  uvicorn 経由の WS でも Nagle 由来の ~40ms バッチ遅延は発生しない。
"""
import asyncio
import logging
import pathlib
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .can_reader import CanReader
from .config import CAN_CHANNEL, HEARTBEAT_SEC, MAX_PUSH_HZ
from .signals import SignalDeriver, build_raw_gauges

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("can-live")

reader: CanReader | None = None
_dirty: asyncio.Event | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # import 時ではなく startup で生成（--reload 時の二重 bus 化を避ける）。
    global reader, _dirty
    loop = asyncio.get_running_loop()
    _dirty = asyncio.Event()
    reader = CanReader()
    reader.start(on_update=lambda: loop.call_soon_threadsafe(_dirty.set))
    log.info("CanReader started on %s", CAN_CHANNEL)
    yield
    if reader is not None:
        reader.stop()


app = FastAPI(title="can-live", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "channel": CAN_CHANNEL,
        "alive": reader.is_alive() if reader else False,
    }


@app.websocket("/api/canlive/ws")
async def canlive_ws(ws: WebSocket):
    await ws.accept()
    deriver = SignalDeriver()
    min_interval = 1.0 / MAX_PUSH_HZ
    await ws.send_json({"type": "ready"})
    try:
        while True:
            # 新フレームが来たら即起床。来なくても HEARTBEAT_SEC ごとに状態を送る
            # （can0 断のとき alive=false をフロントへ伝えるため）。
            try:
                await asyncio.wait_for(_dirty.wait(), timeout=HEARTBEAT_SEC)
                _dirty.clear()
            except asyncio.TimeoutError:
                pass

            raw = reader.snapshot()
            await ws.send_json(
                {
                    "type": "frame",
                    "t": time.time(),
                    "alive": reader.is_alive(),
                    "signals": deriver.build(raw),
                    "raw": build_raw_gauges(raw, reader.db),
                    "frames": reader.raw_frames_snapshot(),  # 校正用：全ID生バイト
                }
            )
            # コアレス上限。新データが洪水でもこの間隔より速くは送らない。
            await asyncio.sleep(min_interval)
    except WebSocketDisconnect:
        pass
    except Exception as e:  # noqa: BLE001
        log.warning("ws closed: %s", e)


# 静的フロント（ビルド済み）を / にマウント。dev では Vite(5273) を使うので無くてもよい。
WEB_DIST = pathlib.Path(__file__).resolve().parent.parent / "web" / "dist"
if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
