import json
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import yt_dlp
from plyer import notification
from yt_dlp.cookies import SUPPORTED_BROWSERS
from yt_dlp.utils import download_range_func

from vega.progress import ProgressSink


def parse_time(value: str) -> float:
    """Accepts 'SS', 'MM:SS', or 'HH:MM:SS'. Raises ValueError otherwise."""
    parts = value.strip().split(":")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"Format de temps invalide : '{value}' (attendu SS, MM:SS ou HH:MM:SS)")
    seconds = 0.0
    for part in parts:
        try:
            number = float(part)
        except ValueError:
            raise ValueError(f"Format de temps invalide : '{value}' (attendu SS, MM:SS ou HH:MM:SS)") from None
        if number < 0 or number != number or number == float("inf"):
            raise ValueError(f"Format de temps invalide : '{value}' (attendu SS, MM:SS ou HH:MM:SS)")
        seconds = seconds * 60 + number
    return seconds


def validate_options(*, audio_only: bool, video_only: bool, quality: Optional[str],
                      start: Optional[str], end: Optional[str],
                      cookies_from_browser: Optional[str] = None) -> None:
    """Raises ValueError with a user-facing message if the option combination is unusable."""
    if audio_only and video_only:
        raise ValueError("--audio et --video-only sont incompatibles")
    if quality is not None and not quality.isdigit():
        raise ValueError(f"Qualité invalide : '{quality}' (attendu un nombre, ex: 720)")
    if cookies_from_browser is not None and cookies_from_browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"Navigateur inconnu : '{cookies_from_browser}' "
                         f"(choix : {', '.join(sorted(SUPPORTED_BROWSERS))})")
    start_sec = parse_time(start) if start else None
    end_sec = parse_time(end) if end else None
    if start_sec is not None and end_sec is not None and start_sec >= end_sec:
        raise ValueError("Le début de l'extrait doit être avant sa fin")


def get_download_path() -> Path:
    return Path.home() / "Downloads"


_HISTORY_LOCK = threading.Lock()


def get_history_file() -> Path:
    return Path.home() / ".vega" / "history.json"


def log_to_history(title: str, url: str, platform: str, download_path: str) -> None:
    history_file = get_history_file()

    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "title": title,
        "url": url,
        "platform": platform,
        "path": download_path,
    }

    # Web jobs run on separate threads: serialize the read-modify-write.
    with _HISTORY_LOCK:
        history = read_history()
        history.append(new_entry)

        history_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = history_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
        os.replace(tmp_file, history_file)


def read_history() -> list[dict]:
    history_file = get_history_file()
    if not history_file.exists():
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


class YDLLogger:
    """Adapts yt-dlp's logger interface to a single error callback."""

    def __init__(self, on_error: Optional[Callable[[str], None]] = None) -> None:
        self._on_error = on_error or (lambda msg: None)

    def debug(self, msg: str) -> None:
        pass

    def info(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass  # e.g. the JS runtime warning — not actionable

    def error(self, msg: str) -> None:
        self._on_error(msg)


def safe_notify(title: str, message: str, timeout: Optional[int] = None) -> None:
    """Desktop notifications are best-effort: a missing backend must never fail a download."""
    try:
        kwargs: dict[str, Any] = {"title": title, "message": message, "app_name": "Vega"}
        if timeout is not None:
            kwargs["timeout"] = timeout
        notification.notify(**kwargs)
    except Exception:
        pass


def cookie_opts(cookies_from_browser: Optional[str]) -> dict[str, Any]:
    return {'cookiesfrombrowser': (cookies_from_browser,)} if cookies_from_browser else {}


def analyze_url(url: str, cookies_from_browser: Optional[str] = None) -> tuple[str, str]:
    opts = {'quiet': True, 'logger': YDLLogger(), **cookie_opts(cookies_from_browser)}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        platform = info.get('extractor_key', 'Divers').capitalize()
        video_title = info.get('title', 'Vidéo inconnue')
    return platform, video_title


def make_progress_hook(sink: ProgressSink) -> Callable[[dict], None]:
    def progress_hook(d: dict) -> None:
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            sink.on_progress(downloaded, total)
    return progress_hook


def make_postprocessor_hook(sink: ProgressSink) -> Callable[[dict], None]:
    def postprocessor_hook(d: dict) -> None:
        if d['status'] == 'started':
            sink.on_processing()
    return postprocessor_hook


def build_ydl_opts(download_dir: Path, progress_hook: Callable[[dict], None], audio_only: bool,
                    video_only: bool, quality: Optional[str], start: Optional[str],
                    end: Optional[str], on_error: Optional[Callable[[str], None]] = None) -> dict[str, Any]:
    ydl_opts: dict[str, Any] = {
        'merge_output_format': 'mp4',
        'outtmpl': str(download_dir / '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
        'logger': YDLLogger(on_error),
    }

    if audio_only:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    elif video_only:
        res_filter = f"[height<=?{quality}]" if quality else ""
        # Prefer a video-only stream, fall back to the best video stream otherwise
        ydl_opts['format'] = f'bestvideo{res_filter}[acodec=none]/bestvideo{res_filter}/best'
        # Force-strip audio in case the fallback stream still carries a track
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
        ydl_opts['postprocessor_args'] = {
            'video-convertor': ['-an'],
            'merger': ['-an']
        }
    else:
        res_filter = f"[height<=?{quality}]" if quality else ""
        ydl_opts['format'] = f'bestvideo{res_filter}+bestaudio/best'

    if start or end:
        start_sec = parse_time(start) if start else 0.0
        end_sec = parse_time(end) if end else float('inf')
        ydl_opts['download_ranges'] = download_range_func(None, [(start_sec, end_sec)])
        ydl_opts['force_keyframes_at_cuts'] = True

    return ydl_opts


def run_download(url: str, sink: ProgressSink, *, audio_only: bool = False, video_only: bool = False,
                  quality: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None,
                  output_dir: Optional[Path] = None, cookies_from_browser: Optional[str] = None) -> bool:
    """Shared entry point for the CLI and the web backend — all state flows through `sink`.

    Returns True on success, False if the download failed (already reported to `sink`).
    """
    try:
        validate_options(audio_only=audio_only, video_only=video_only, quality=quality, start=start, end=end,
                         cookies_from_browser=cookies_from_browser)
    except ValueError as e:
        sink.on_error(str(e))
        return False

    if shutil.which("ffmpeg") is None:
        sink.on_error("FFmpeg est introuvable. Installe-le et ajoute-le au PATH : https://ffmpeg.org/download.html")
        return False

    sink.on_analyzing()

    try:
        platform, video_title = analyze_url(url, cookies_from_browser)
    except Exception as e:
        sink.on_error(f"Erreur d'analyse : {e}")
        safe_notify("Vega - Erreur", "Impossible d'analyser l'URL")
        return False

    download_dir = output_dir if output_dir is not None else get_download_path() / platform
    try:
        download_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sink.on_error(f"Impossible de créer le dossier '{download_dir}' : {e}")
        return False

    sink.on_start(platform, video_title, download_dir)

    progress_hook = make_progress_hook(sink)
    ydl_opts = build_ydl_opts(download_dir, progress_hook, audio_only, video_only, quality, start, end,
                               on_error=sink.on_error)
    ydl_opts['postprocessor_hooks'] = [make_postprocessor_hook(sink)]
    ydl_opts.update(cookie_opts(cookies_from_browser))

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        log_to_history(video_title, url, platform, str(download_dir))
        sink.on_finished(video_title)

        safe_notify("Vega - Succès", f"Terminé : {video_title}", timeout=5)
        return True
    except Exception as e:
        sink.on_error(f"Erreur : {e}")
        safe_notify("Vega - Erreur", str(e))
        return False
