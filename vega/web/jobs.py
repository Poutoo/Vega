import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from vega.core import run_download


@dataclass
class Job:
    id: str
    queue: "asyncio.Queue[dict]" = field(default_factory=asyncio.Queue)


class WebSocketProgressSink:
    """Relays progress events to a Job's asyncio queue.

    yt-dlp runs its hooks on the executor thread, not the event loop, so each
    call must be scheduled via call_soon_threadsafe rather than touching the
    queue directly.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, queue: "asyncio.Queue[dict]") -> None:
        self._loop = loop
        self._queue = queue

    def _push(self, event: dict) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def on_analyzing(self) -> None:
        self._push({"type": "analyzing"})

    def on_start(self, platform: str, title: str, download_dir: Path) -> None:
        self._push({"type": "start", "platform": platform, "title": title, "path": str(download_dir)})

    def on_progress(self, downloaded: int, total: Optional[int]) -> None:
        self._push({"type": "progress", "downloaded": downloaded, "total": total})

    def on_processing(self) -> None:
        self._push({"type": "processing"})

    def on_finished(self, title: str) -> None:
        self._push({"type": "finished", "title": title})

    def on_error(self, message: str) -> None:
        self._push({"type": "error", "message": message})


JOBS: dict[str, Job] = {}


def create_job(url: str, *, audio_only: bool, video_only: bool, quality: Optional[str],
                start: Optional[str], end: Optional[str]) -> Job:
    job = Job(id=uuid.uuid4().hex)
    JOBS[job.id] = job

    loop = asyncio.get_running_loop()
    sink = WebSocketProgressSink(loop, job.queue)

    def worker() -> None:
        try:
            run_download(url, sink, audio_only=audio_only, video_only=video_only,
                         quality=quality, start=start, end=end)
        except Exception as e:  # never leave the UI waiting on a dead worker
            sink.on_error(f"Erreur inattendue : {e}")
        finally:
            loop.call_soon_threadsafe(job.queue.put_nowait, {"type": "closed"})

    threading.Thread(target=worker, daemon=True).start()
    return job
