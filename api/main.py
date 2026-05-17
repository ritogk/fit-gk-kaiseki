"""FastAPI entry point.

Mounts /api/control/*, /api/fun/* routers and serves the Vue 3 frontend
from /web at the root.
"""
import pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .control import router as control_router
from .fun import router as fun_router
from .live import router as live_router

app = FastAPI(
    title="Fit GK Kaiseki",
    description="Research API for Honda Fit GK5 K-Line ECM(0x10) IO Control. "
                "For own-vehicle research / educational use only.",
    version="0.1.0",
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
WEB_DIR = pathlib.Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
