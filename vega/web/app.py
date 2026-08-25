from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from vega.core import read_history
from vega.web.jobs import JOBS, create_job

STATIC_DIR = Path(__file__).parent / "static"


class DownloadRequest(BaseModel):
    url: str
    audio_only: bool = False
    video_only: bool = False
    quality: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None


def create_app() -> FastAPI:
    app = FastAPI(title="Vega")

    @app.post("/api/download")
    async def start_download(req: DownloadRequest) -> dict:
        job = create_job(
            req.url,
            audio_only=req.audio_only,
            video_only=req.video_only,
            quality=req.quality,
            start=req.start,
            end=req.end,
        )
        return {"job_id": job.id}

    @app.get("/api/history")
    async def history() -> list[dict]:
        return read_history()

    @app.websocket("/ws/progress/{job_id}")
    async def progress_ws(websocket: WebSocket, job_id: str) -> None:
        job = JOBS.get(job_id)
        if job is None:
            await websocket.close(code=4404)
            return

        await websocket.accept()
        try:
            while True:
                event = await job.queue.get()
                if event["type"] == "closed":
                    break
                await websocket.send_json(event)
            await websocket.close()
        except WebSocketDisconnect:
            pass
        finally:
            JOBS.pop(job_id, None)

    # Mounted last so the /api and /ws routes above take precedence.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app
