"""Control router — individual K-Line commands.

Each endpoint connects, fires, and disconnects (~600ms). Long fire envelopes
are held until done, then StopDiag is sent for a hard cutoff.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException

from kline.client import KLineClient, KLineBusyError
from kline.commands import LIDS, fire, list_commands

router = APIRouter(prefix="/api/control", tags=["control"])


@router.get("/list")
def get_list():
    """Return all known commands and their LID/IOCP map."""
    return list_commands()


@router.post("/stop_all")
def post_stop_all():
    """Send StopDiagSession to kill any active IO Control envelopes."""
    try:
        with KLineClient() as cli:
            cli.stop_diag()
    except KLineBusyError as e:
        raise HTTPException(409, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return {"status": "ok"}


@router.post("/{name}")
def post_fire(name: str, duration_s: Optional[float] = None):
    if name not in LIDS:
        raise HTTPException(404, f"unknown command: {name}")
    try:
        result = fire(name, duration_s)
    except KLineBusyError as e:
        raise HTTPException(409, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return {"command": name, "duration_s": duration_s, "result": result}
