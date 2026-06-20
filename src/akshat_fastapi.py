from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
load_dotenv()  # Load .env file before importing backend modules

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.api.routes import get_current_user, router as auth_router
from backend.app.utils.safeguards import WorkflowGuardrails

try:
    from akshat_local import AkshatCore, EventBus, MemoryStore, DB_PATH, HOST, PORT
except ModuleNotFoundError:
    from src.akshat_local import AkshatCore, EventBus, MemoryStore, DB_PATH, HOST, PORT


SRC = Path(__file__).resolve().parent

memory = MemoryStore(DB_PATH)
bus = EventBus()
core = AkshatCore(memory, bus)

# Issue 1: per-IP workflow rate limiter (in-process; swap for Redis in prod).
_workflow_guardrails = WorkflowGuardrails.from_settings()


def _check_workflow_rate_limit(request: Request) -> None:
    """Throttle expensive workflow submissions per client IP."""
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = _workflow_guardrails.limiter.check(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Workflow rate limit exceeded. Max {_workflow_guardrails.limiter.max_requests} "
                   f"per {_workflow_guardrails.limiter.window_seconds}s. Try again later.",
            headers={"Retry-After": str(_workflow_guardrails.limiter.window_seconds)},
        )


app = FastAPI(title="AKSHAT Autonomous Engineering OS")
app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets", StaticFiles(directory=ROOT / "workspace"), name="assets")


@app.get("/api/status")
def status(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return core.snapshot()


@app.get("/api/memory")
def memory_items(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return {"items": core.memory.recent(50)}


@app.get("/api/logs")
def logs(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    workflow = core.snapshot().get("workflow", {})
    return {"events": workflow.get("execution_trace", workflow.get("events", []))}


@app.get("/api/tool-logs")
def tool_logs(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return {"items": core.memory.recent_tool_logs(100)}


@app.get("/api/plan")
def plan(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    snapshot = core.snapshot()
    return {"plan": snapshot.get("plan", []), "todo_list": snapshot.get("todo_list", [])}


@app.get("/api/git")
def git(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return core.snapshot().get("git", {})


@app.get("/api/browser")
def browser(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return core.snapshot().get("browser", {})


@app.get("/api/artifacts")
def artifacts(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    snapshot = core.snapshot()
    return {
        "items": snapshot.get("artifact_history", []),
        "deployment_url": snapshot.get("deployment_url", ""),
        "artifact_name": snapshot.get("artifact_name", ""),
        "artifact_version": snapshot.get("artifact_version", ""),
    }


@app.get("/api/tools")
def tools(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return {"tools": core.tool_catalog(), "active": core.snapshot().get("active_tools", [])}


@app.post("/api/task")
def submit_task(payload: Dict[str, Any], request: Request, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _check_workflow_rate_limit(request)
    try:
        user_id = current_user.get("user_id", 1)
        workflow_pattern = str(payload.get("workflow_pattern", "Auto"))
        return core.submit(str(payload.get("prompt", "")), user_id=user_id, workflow_pattern=workflow_pattern)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat")
def chat(payload: Dict[str, Any], request: Request, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _check_workflow_rate_limit(request)
    try:
        user_id = current_user.get("user_id", 1)
        workflow_pattern = str(payload.get("workflow_pattern", "Auto"))
        return core.chat(str(payload.get("message", "")), user_id=user_id, workflow_pattern=workflow_pattern)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/tool")
def run_tool(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    tool_args = payload.get("args", {})
    if not isinstance(tool_args, dict):
        tool_args = {}
    try:
        return core.execute_tool(str(payload.get("tool", "")), tool_args)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/store-memory")
def store_memory(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    core.store_memory(
        str(payload.get("kind", "note")),
        str(payload.get("prompt", "")),
        str(payload.get("summary", "")),
        payload.get("payload", {}),
    )
    return {"ok": True}

# Obsolete JS scripts and html string endpoints deleted. Serving compiled SPA instead.


def _escape_html(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _safe_artifact_name(name: str) -> str:
    return "".join(ch for ch in name if ch.isalnum() or ch in {"_", "-"})


def _project_files(safe_name: str) -> list[Dict[str, str]]:
    project_dir = ROOT / "workspace" / "projects" / safe_name
    if not project_dir.exists():
        return []
    files: list[Dict[str, str]] = []
    for path in sorted(project_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(project_dir).as_posix()
            files.append({"path": rel, "source": path.read_text(encoding="utf-8")})
    return files


def _legacy_artifact_path(safe_name: str) -> Path:
    return ROOT / "workspace" / "projects" / f"{safe_name}.html"


def _with_project_base(source: str, safe_name: str) -> str:
    base = f'<base href="/assets/projects/{safe_name}/">'
    lower = source.lower()
    if "<head>" in lower:
        index = lower.find("<head>") + len("<head>")
        return source[:index] + base + source[index:]
    return base + source


def _artifact_page(safe_name: str, mode: str) -> HTMLResponse:
    files = _project_files(safe_name)
    review_url = f"/review/{safe_name}"
    deploy_url = f"/deploy/{safe_name}"
    if files:
        index = next((item for item in files if item["path"] == "index.html"), files[0])
        if mode == "deploy":
            return HTMLResponse(_with_project_base(index["source"], safe_name))
        artifact_url = deploy_url
        initial_source = index["source"]
        source_payload = json.dumps(files)
    else:
        path = _legacy_artifact_path(safe_name)
        if not path.exists():
            raise HTTPException(status_code=404, detail="artifact not found")
        source = path.read_text(encoding="utf-8")
        if mode == "deploy":
            return HTMLResponse(source)
        artifact_url = f"/assets/{safe_name}.html"
        initial_source = source
        source_payload = json.dumps([{"path": f"{safe_name}.html", "source": source}])

    escaped = _escape_html(initial_source)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{mode.title()} {safe_name} | AKSHAT</title>
  <style>
    :root{{--bg:#03050b;--panel:rgba(8,13,25,.78);--line:rgba(255,255,255,.14);--text:#f8fafc;--muted:#91a1b6;--cyan:#38d5ff;--green:#4cf2a1}}
    *{{box-sizing:border-box}}
    body{{margin:0;min-height:100vh;background:radial-gradient(circle at 20% 20%,rgba(56,213,255,.15),transparent 28%),linear-gradient(145deg,#02040a,#07111c);color:var(--text);font-family:"Aptos","Segoe UI",system-ui,sans-serif}}
    header{{height:72px;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:0 24px;border-bottom:1px solid var(--line);background:rgba(3,7,14,.78);backdrop-filter:blur(16px)}}
    h1{{margin:0;font-family:"Bahnschrift","Segoe UI",system-ui,sans-serif;font-size:1.05rem;letter-spacing:.08em;text-transform:uppercase}}
    .actions{{display:flex;gap:10px;flex-wrap:wrap}}
    button,a{{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:rgba(255,255,255,.06);color:var(--text);font-weight:800;text-decoration:none;cursor:pointer}}
    .primary{{border:0;background:linear-gradient(135deg,var(--cyan),var(--green));color:#031016}}
    main{{height:calc(100vh - 72px);display:grid;grid-template-columns:minmax(0,1.15fr) minmax(380px,.85fr);gap:16px;padding:16px}}
    .panel{{min-height:0;border:1px solid var(--line);border-radius:8px;background:var(--panel);box-shadow:0 24px 70px rgba(0,0,0,.35);overflow:hidden}}
    iframe{{width:100%;height:100%;border:0;background:#fff}}
    .code{{display:grid;grid-template-rows:auto auto 1fr auto;height:100%}}
    .code-head,.file-tabs{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 14px;border-bottom:1px solid var(--line);color:var(--muted);font-size:.85rem}}
    .file-tabs{{justify-content:flex-start;overflow:auto}}
    .file-tabs button{{white-space:nowrap}}
    .file-tabs button.active{{background:linear-gradient(135deg,var(--cyan),var(--green));color:#031016;border:0}}
    textarea{{width:100%;height:100%;resize:none;border:0;outline:0;padding:16px;background:#050913;color:#dffaff;font:13px/1.55 Consolas,"Cascadia Code",monospace}}
    .meta{{display:grid;gap:8px;padding:12px 14px;border-top:1px solid var(--line);color:var(--muted);font-size:.85rem}}
    .meta strong{{color:var(--text)}}
    @media(max-width:900px){{main{{height:auto;grid-template-columns:1fr}}.panel{{height:70vh}}.code{{height:70vh}}}}
  </style>
</head>
<body>
  <header>
    <h1>AKSHAT {mode.title()}: {safe_name}</h1>
    <div class="actions">
      <a href="/">Back to AKSHAT</a>
      <a class="primary" href="{deploy_url}" target="_blank" rel="noreferrer">Open Visual Deploy</a>
      <a href="{review_url}" target="_blank" rel="noreferrer">Review Source</a>
      <button type="button" onclick="copyCode()">Copy Source</button>
      <button type="button" onclick="copyUrl()">Copy URL</button>
      <button type="button" onclick="downloadSource()">Download</button>
    </div>
  </header>
  <main>
    <section class="panel"><iframe src="{artifact_url}" title="Artifact preview"></iframe></section>
    <section class="panel code">
      <div class="code-head"><strong>Source</strong><span id="copy-status">Ready to copy</span></div>
      <div class="file-tabs" id="file-tabs"></div>
      <textarea id="source" spellcheck="false">{escaped}</textarea>
      <div class="meta">
        <div><strong>Artifact</strong> <span>{safe_name}</span></div>
        <div><strong>Preview</strong> <span>{deploy_url}</span></div>
        <div><strong>Review</strong> <span>{review_url}</span></div>
        <div><strong>Deploy</strong> <span>{deploy_url}</span></div>
      </div>
    </section>
  </main>
  <script>
    const files = {source_payload};
    let selectedFile = files[0] || {{ path: 'source', source: '' }};
    function renderTabs(){{
      const tabs = document.getElementById('file-tabs');
      tabs.innerHTML = '';
      files.forEach((file) => {{
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = file.path;
        button.className = file.path === selectedFile.path ? 'active' : '';
        button.onclick = () => {{
          selectedFile = file;
          document.getElementById('source').value = file.source;
          renderTabs();
        }};
        tabs.appendChild(button);
      }});
    }}
    async function copyCode(){{
      const source = document.getElementById('source');
      source.select();
      try {{
        await navigator.clipboard.writeText(source.value);
        document.getElementById('copy-status').textContent = 'Copied source';
      }} catch {{
        document.execCommand('copy');
        document.getElementById('copy-status').textContent = 'Copied source';
      }}
    }}
    async function copyUrl(){{
      try {{
        await navigator.clipboard.writeText(window.location.href);
        document.getElementById('copy-status').textContent = 'Copied URL';
      }} catch {{
        document.getElementById('copy-status').textContent = 'Copy failed';
      }}
    }}
    function downloadSource(){{
      const blob = new Blob([document.getElementById('source').value], {{ type: 'text/html' }});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = selectedFile.path.split('/').pop() || '{safe_name}.html';
      link.click();
      URL.revokeObjectURL(link.href);
    }}
    renderTabs();
  </script>
</body>
</html>"""
    return HTMLResponse(html)


@app.get("/api/artifact/source/{name}")
def artifact_source(name: str) -> Dict[str, Any]:
    safe_name = _safe_artifact_name(name)
    files = _project_files(safe_name)
    if files:
        return {"name": safe_name, "path": f"src/assets/projects/{safe_name}", "files": files, "source": files[0]["source"]}
    path = _legacy_artifact_path(safe_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact not found")
    return {"name": safe_name, "path": f"src/assets/{safe_name}.html", "source": path.read_text(encoding="utf-8")}


@app.get("/review/{name}")
def review_artifact(name: str) -> HTMLResponse:
    safe_name = _safe_artifact_name(name)
    return _artifact_page(safe_name, "review")


@app.get("/deploy/{name}")
def deploy_artifact(name: str) -> HTMLResponse:
    safe_name = _safe_artifact_name(name)
    return _artifact_page(safe_name, "deploy")


@app.websocket("/ws")
async def websocket(websocket: WebSocket, token: str | None = None) -> None:
    from backend.api.routes import decode_jwt_token
    if not token or not decode_jwt_token(token):
        await websocket.accept()
        await websocket.send_text(json.dumps({"ts": "live", "kind": "error", "message": "Unauthorized WebSocket connection."}))
        await websocket.close(code=1008)
        return
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


# Serve the compiled React SPA
FRONTEND_DIST = ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/{active:path}")
    def page(active: str = ""):
        return {"message": "Frontend not built yet. Run 'npm run build' inside the 'frontend' directory."}


def main() -> None:
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
