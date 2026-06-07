from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from akshat_local import AkshatCore, EventBus, MemoryStore, DB_PATH, HOST, PORT
    from akshat_views import render_page
except ModuleNotFoundError:
    from src.akshat_local import AkshatCore, EventBus, MemoryStore, DB_PATH, HOST, PORT
    from src.akshat_views import render_page


SRC = Path(__file__).resolve().parent

memory = MemoryStore(DB_PATH)
bus = EventBus()
core = AkshatCore(memory, bus)

app = FastAPI(title="AKSHAT Autonomous Engineering OS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets", StaticFiles(directory=SRC / "assets"), name="assets")


@app.get("/api/status")
def status() -> Dict[str, Any]:
    return core.snapshot()


@app.get("/api/memory")
def memory_items() -> Dict[str, Any]:
    return {"items": core.memory.recent(50)}


@app.get("/api/logs")
def logs() -> Dict[str, Any]:
    events = core.snapshot().get("workflow", {}).get("events", [])
    return {"events": events}


@app.get("/api/tool-logs")
def tool_logs() -> Dict[str, Any]:
    return {"items": core.memory.recent_tool_logs(100)}


@app.get("/api/plan")
def plan() -> Dict[str, Any]:
    snapshot = core.snapshot()
    return {"plan": snapshot.get("plan", []), "todo_list": snapshot.get("todo_list", [])}


@app.get("/api/git")
def git() -> Dict[str, Any]:
    return core.snapshot().get("git", {})


@app.get("/api/browser")
def browser() -> Dict[str, Any]:
    return core.snapshot().get("browser", {})


@app.get("/api/tools")
def tools() -> Dict[str, Any]:
    return {"tools": core.tool_catalog(), "active": core.snapshot().get("active_tools", [])}


@app.post("/api/task")
def submit_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return core.submit(str(payload.get("prompt", "")))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat")
def chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return core.chat(str(payload.get("message", "")))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/tool")
def run_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    tool_args = payload.get("args", {})
    if not isinstance(tool_args, dict):
        tool_args = {}
    try:
        return core.execute_tool(str(payload.get("tool", "")), tool_args)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/store-memory")
def store_memory(payload: Dict[str, Any]) -> Dict[str, Any]:
    core.store_memory(
        str(payload.get("kind", "note")),
        str(payload.get("prompt", "")),
        str(payload.get("summary", "")),
        payload.get("payload", {}),
    )
    return {"ok": True}


@app.get("/avatar_runtime.js")
def avatar_runtime() -> Response:
    return Response((SRC / "avatar_runtime.js").read_text(encoding="utf-8"), media_type="application/javascript")


@app.get("/react_dashboard.js")
def react_dashboard() -> Response:
    path = SRC / "dashboard" / "App.jsx"
    return Response(path.read_text(encoding="utf-8"), media_type="application/javascript")


@app.get("/react")
def react_page() -> HTMLResponse:
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AKSHAT React Dashboard</title>
  <style>body{margin:0;background:#05070c;color:#e5e7eb;font-family:"JetBrains Mono",Consolas,monospace}.content{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:16px;padding:16px}.panel{border:1px solid rgba(255,255,255,.08);background:rgba(10,14,24,.78);border-radius:8px;padding:16px}.span-12{grid-column:span 12}.span-6{grid-column:span 6}.label{color:#93a3b8;text-transform:uppercase;font-size:.78rem}.value{font-size:1.2rem}.stat,.agent-card{border:1px solid rgba(255,255,255,.08);padding:12px;border-radius:8px}.workflow-strip,.agent-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.agent-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.console{white-space:pre-wrap;max-height:420px;overflow:auto;background:#02040a;padding:12px;border-radius:8px}input{width:100%;box-sizing:border-box;margin:10px 0;padding:12px;background:#02040a;color:#fff;border:1px solid rgba(255,255,255,.12);border-radius:8px}button{padding:10px 14px;border:0;border-radius:8px;background:#22d3ee;color:#031016;font-weight:700}@media(max-width:900px){.span-6,.span-12{grid-column:span 12}.workflow-strip,.agent-grid{grid-template-columns:1fr}}</style>
</head>
<body>
  <div id="react-root"></div>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="/react_dashboard.js"></script>
</body>
</html>"""
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    q = bus.subscribe()
    await websocket.send_text(json.dumps({"ts": "live", "kind": "ready", "message": "AKSHAT websocket connected.", "data": core.snapshot()}))
    try:
        while True:
            try:
                payload = await asyncio.to_thread(q.get, True, 0.5)
                await websocket.send_text(payload)
            except Exception:
                await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        bus.unsubscribe(q)


@app.get("/{active:path}")
def page(active: str = "avatar") -> HTMLResponse:
    active = active.split("?")[0].strip("/") or "avatar"
    if active not in {"avatar", "agents", "terminal", "plan", "repo", "memory", "browser", "tests", "git", "status"}:
        active = "avatar"
    html = render_page(
        "AKSHAT",
        active,
        core.snapshot(),
        os.environ.get("AKSHAT_THEME", "cyan"),
        os.environ.get("AKSHAT_DENSITY", "normal"),
    )
    return HTMLResponse(html)


def main() -> None:
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
