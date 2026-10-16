from pathlib import Path
from typing import Optional, Protocol

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

PINK = "#F7B6C2"        # primary accent (borders, highlights)
PINK_DEEP = "#F48FB1"   # titles, emphasis
PINK_LIGHT = "#FADDE1"  # secondary text


class ProgressSink(Protocol):
    """Target `run_download` reports to, regardless of caller (CLI, web)."""

    def on_analyzing(self) -> None: ...
    def on_start(self, platform: str, title: str, download_dir: Path) -> None: ...
    def on_progress(self, downloaded: int, total: Optional[int]) -> None: ...
    def on_processing(self) -> None: ...
    def on_finished(self, title: str) -> None: ...
    def on_error(self, message: str) -> None: ...


class RichProgressSink:
    def __init__(self, console: Console) -> None:
        self.console = console
        self.progress = Progress(
            SpinnerColumn(style=PINK),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None, pulse_style=PINK, complete_style=PINK_DEEP, finished_style=PINK_DEEP),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            expand=True,
        )
        self.task_id = self.progress.add_task(f"[bold {PINK_DEEP}]Téléchargement...", total=None)

    def on_analyzing(self) -> None:
        self.console.print(f"[bold {PINK_DEEP}]Analyse de l'URL en cours...[/]")

    def on_start(self, platform: str, title: str, download_dir: Path) -> None:
        self.console.print(f"[bold {PINK_DEEP}][+][/] Plateforme : [bold {PINK}]{platform}[/]")
        self.console.print(f"[bold {PINK_DEEP}][+][/] Titre : [{PINK_LIGHT}]{title}[/]")
        self.console.print(f"[bold {PINK_DEEP}][+][/] Dossier : [{PINK_LIGHT}]{download_dir}[/]\n")

    def on_progress(self, downloaded: int, total: Optional[int]) -> None:
        self.progress.update(self.task_id, completed=downloaded, total=total)

    def on_processing(self) -> None:
        self.progress.update(self.task_id, description=f"[bold {PINK_DEEP}]Traitement (FFmpeg)...", total=None)

    def on_finished(self, title: str) -> None:
        self.progress.update(self.task_id, completed=100, total=100, description="[bold green]Terminé !")
        self.console.print(f"\n[bold green]✔[/bold green] [bold {PINK_DEEP}]Téléchargement réussi :[/] {title}")

    def on_error(self, message: str) -> None:
        self.console.print(f"\n[bold red]✘[/bold red] {message}")
