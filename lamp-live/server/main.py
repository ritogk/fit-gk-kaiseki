"""lamp-live サーバ。画面(WebSocket) → 照明エンジン → シリアル → ESP32 → ハイビーム左右。

起動: lamp-live/run.sh  (http://localhost:8200/)
"""
import asyncio
import contextlib
import json
import pathlib
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config, patterns
from .engine import Engine
from .serial_link import SerialLink

WEB = pathlib.Path(__file__).resolve().parent.parent / "web"

engine = Engine()
link: SerialLink | None = None
clients: set[WebSocket] = set()


def state_msg():
    s = engine.snapshot()
    s["t"] = "state"
    s["serial"] = {"connected": bool(link and link.connected),
                   "port": link.port if link else None,
                   "last": link.last_line if link else ""}
    return json.dumps(s)


async def engine_loop():
    period = 1.0 / config.ENGINE_HZ
    last = time.monotonic()
    while True:
        now = time.monotonic()
        dt, last = now - last, now
        r, l = engine.tick(dt)
        if link:
            await asyncio.to_thread(link.set_lr, r, l)
        await asyncio.sleep(max(0.0, period - (time.monotonic() - now)))


async def push_loop():
    while True:
        if clients:
            msg = state_msg()
            for ws in list(clients):
                try:
                    await ws.send_text(msg)
                except Exception:
                    clients.discard(ws)
        await asyncio.sleep(1.0 / config.PUSH_HZ)


@contextlib.asynccontextmanager
async def lifespan(app):
    global link
    link = SerialLink()
    tasks = [asyncio.create_task(engine_loop()), asyncio.create_task(push_loop())]
    try:
        yield
    finally:
        for t in tasks:
            t.cancel()
        link.shutdown()  # 終了時は必ず全消灯し、フェードを 300ms に戻す


app = FastAPI(lifespan=lifespan)


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/api/patterns")
def list_patterns():
    return [{"key": p.key, "label": p.label} for p in patterns.ALL]


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    await ws.send_text(state_msg())
    try:
        while True:
            try:
                m = json.loads(await ws.receive_text())
            except json.JSONDecodeError:
                continue
            if isinstance(m, dict):
                engine.handle(m)
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)
        # 押しっぱなしのまま画面が落ちたときに点きっぱなしにしない
        engine.bump = False


app.mount("/static", StaticFiles(directory=WEB), name="static")
