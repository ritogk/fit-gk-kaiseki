"""WebSocket endpoint for live performance mode.

Maintains a persistent K-Line session and translates JSON messages
to note_on/note_off commands with minimal latency.
"""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from kline.live import start_session, stop_session, get_session

router = APIRouter(prefix="/api/live", tags=["live"])


@router.websocket("/ws")
async def live_ws(ws: WebSocket):
    await ws.accept()
    session = None
    should_stop = False
    try:
        session = start_session()
        await ws.send_json({"type": "ready"})
    except RuntimeError as e:
        await ws.send_json({"type": "error", "message": str(e)})
        await ws.close()
        return

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            cmd_id = msg.get("id", "")

            if msg_type == "ping":
                await ws.send_json({"type": "pong"})
                continue
            if msg_type == "exit":
                should_stop = True
                break

            # コマンド処理前にセッションの生存を確認。ワーカーがシリアル異常で
            # 死んでいたら作り直し、再起動なしでユーザー操作だけで復旧させる。
            if not session.is_alive():
                try:
                    session = start_session()
                    await ws.send_json({"type": "ready"})
                except RuntimeError as e:
                    await ws.send_json({"type": "error", "message": str(e)})
                    continue

            if msg_type == "note_on":
                session.note_on(cmd_id)
            elif msg_type == "note_off":
                session.note_off(cmd_id)
            elif msg_type == "all_off":
                session.all_off()
            elif msg_type == "loop_on":
                session.loop_on(cmd_id)
            elif msg_type == "loop_off":
                session.loop_off(cmd_id)
            elif msg_type == "bpm":
                session.set_bpm(float(msg.get("bpm", 120)))
            else:
                continue

            await ws.send_json({
                "type": "state",
                "active": list(session.get_active()),
            })

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if should_stop:
            stop_session()
