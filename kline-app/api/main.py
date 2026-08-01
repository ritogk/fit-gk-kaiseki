"""FastAPI entry point.

Mounts /api/control/*, /api/fun/* routers and serves the Vue 3 frontend
from /web at the root.
"""
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from kline.live import stop_session

from .control import router as control_router
from .fun import router as fun_router
from .live import router as live_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # サーバ終了時(uvicorn --reload の再読み込み含む)に K-Line セッションを確実に
    # 閉じる。StopDiag 送信 → シリアルポート close → ロック解放を行い、旧プロセスが
    # ポートを掴んだまま残って次プロセスが開けなくなる事態を防ぐ。
    stop_session()


app = FastAPI(
    title="Fit GK Kaiseki",
    description="Research API for Honda Fit GK5 K-Line ECM(0x10) IO Control. "
                "For own-vehicle research / educational use only.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(control_router)
app.include_router(fun_router)
app.include_router(live_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Static frontend at /
WEB_DIST = pathlib.Path(__file__).resolve().parent.parent / "web" / "dist"
if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
