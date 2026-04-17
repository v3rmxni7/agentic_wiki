# FastAPI app: serves the single-page frontend and the JSON/SSE endpoints.
from __future__ import annotations

import json
import queue
import threading
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from backend.orchestrator import run as run_orchestrator
from backend.schemas import QueryRequest, TraceEvent
from backend.tools import graph as graph_tool
from backend.tools import notes as notes_tool

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

app = FastAPI(title="Agentic Wiki")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/api/notes")
def api_notes():
    li = graph_tool.links_in_map()
    notes = notes_tool.list_notes(links_in_map=li)
    return {"notes": [n.model_dump() for n in notes]}


@app.get("/api/note/{slug}")
def api_note(slug: str):
    post = notes_tool.read_raw(slug)
    if not post:
        raise HTTPException(404, f"note {slug} not found")
    li = graph_tool.links_in_map().get(slug, 0)
    meta = notes_tool.meta_from_post(slug, post, links_in=li)
    return {"meta": meta.model_dump(), "body": post.content}


@app.get("/api/graph")
def api_graph():
    return graph_tool.build_graph()


@app.post("/api/query")
def api_query(req: QueryRequest):
    result = run_orchestrator(req.query)
    return result.model_dump()


@app.get("/api/query_stream")
def api_query_stream(query: str):
    # SSE endpoint: streams each agent's start/end as a `trace` event, then a final
    # `result` event with the full response. The orchestrator runs on a worker
    # thread so the generator can yield as events arrive.
    q: "queue.Queue[tuple[str, dict]]" = queue.Queue()

    def cb(event: TraceEvent) -> None:
        q.put(("trace", event.model_dump()))

    def worker():
        try:
            result = run_orchestrator(query, trace_cb=cb)
            q.put(("result", result.model_dump()))
        except Exception as e:
            q.put(("error", {"message": str(e)}))
        finally:
            q.put(("done", {}))

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    def stream():
        while True:
            kind, payload = q.get()
            yield f"event: {kind}\ndata: {json.dumps(payload)}\n\n"
            if kind == "done":
                break

    return StreamingResponse(stream(), media_type="text/event-stream")


if (FRONTEND / "static").exists():
    app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")
