import yt_dlp
import argparse
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from yt_dlp.utils import download_range_func

# Interface Moderne
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn, SpinnerColumn
from rich.status import Status
# pyrefly: ignore [missing-import]
from plyer import notification

# Initialisation de la console Rich
console = Console()

def parse_time(value: str) -> float:
    """Convertit un timestamp ('SS', 'MM:SS' ou 'HH:MM:SS') en secondes."""
    seconds = 0.0
    for part in value.split(":"):
        seconds = seconds * 60 + float(part)
    return seconds

def get_download_path() -> Path:
    """Retourne le chemin vers le dossier Downloads de l'utilisateur."""
    return Path.home() / "Downloads"

def log_to_history(title: str, url: str, platform: str, download_path: str) -> None:
    """Enregistre les détails du téléchargement dans history.json."""
    history_file = Path("history.json")
    
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "title": title,
        "url": url,
        "platform": platform,
        "path": download_path
    }
    
    history = []
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    history.append(new_entry)
    
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        console.print(f"[bold red][/!\\] Impossible d'écrire l'historique : {e}[/bold red]")

class YDLLogger:
    """Logger personnalisé pour rediriger les sorties de yt-dlp vers la console Rich."""
    def debug(self, msg):
        if msg.startswith('[debug] '): pass
        else: self.info(msg)
    def info(self, msg): pass
    def warning(self, msg): pass # Ignorer les avertissements (comme le JS runtime)
    def error(self, msg):
        console.print(f"[bold red]✘ {msg}[/bold red]")

def run_vega(url: str, audio_only: bool = False, video_only: bool = False, quality: Optional[str] = None,
             start: Optional[str] = None, end: Optional[str] = None) -> None:
    """Télécharge une vidéo ou de l'audio avec une interface moderne et tri par plateforme."""
    
    console.print(Panel.fit(
        "[bold cyan]VEGA[/bold cyan] [white]v1.1 - Downloader Universel[/white]",
        border_style="bright_blue"
    ))

    # Phase 1 : Analyse
    with Status("[bold yellow]Analyse de l'URL en cours...", spinner="dots") as status:
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'logger': YDLLogger()}) as ydl:
                info = ydl.extract_info(url, download=False)
                platform = info.get('extractor_key', 'Divers').capitalize()
                video_title = info.get('title', 'Vidéo inconnue')
        except Exception as e:
            console.print(f"[bold red][/!\\] Erreur d'analyse : {e}")
            notification.notify(title="Vega - Erreur", message="Impossible d'analyser l'URL", app_name="Vega")
            return

    download_dir = get_download_path() / platform
    download_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold green][+][/bold green] Plateforme : [bold magenta]{platform}[/bold magenta]")
    console.print(f"[bold green][+][/bold green] Titre : [cyan]{video_title}[/cyan]")
    console.print(f"[bold green][+][/bold green] Dossier : [blue]{download_dir}[/blue]\n")

    # Barre de progression personnalisée
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None, pulse_style="cyan"),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        expand=True
    )

    task_id = progress.add_task("[bold cyan]Téléchargement...", total=None)

    def progress_hook(d):
        if d['status'] == 'downloading':
            p = d.get('downloaded_bytes', 0)
            t = d.get('total_bytes') or d.get('total_bytes_estimate')
            if t:
                progress.update(task_id, completed=p, total=t)
            else:
                progress.update(task_id, completed=p, total=None) # Mode indéterminé si pas de taille
        elif d['status'] == 'finished':
            progress.update(task_id, completed=100, total=100, description="[bold green]Terminé !")

    # Configuration yt-dlp
    ydl_opts = {
        'merge_output_format': 'mp4',
        'outtmpl': str(download_dir / '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
        'logger': YDLLogger(),
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
        # On cherche d'abord un flux sans audio, sinon on prend le meilleur flux vidéo
        ydl_opts['format'] = f'bestvideo{res_filter}[acodec=none]/bestvideo{res_filter}/best'
        # On force un post-traitement pour supprimer l'audio au cas où le flux en contient
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
        console.print(f"[bold green][+][/bold green] Extrait : [yellow]{start or '0:00'} → {end or 'fin'}[/yellow]\n")

    try:
        with progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        
        # Enregistrement et Notification
        log_to_history(video_title, url, platform, str(download_dir))
        
        console.print(f"\n[bold green]✔[/bold green] [bold white]Téléchargement réussi :[/bold white] {video_title}")
        
        notification.notify(
            title="Vega - Succès",
            message=f"Terminé : {video_title}",
            app_name="Vega",
            timeout=5
        )
    except Exception as e:
        console.print(f"\n[bold red]✘[/bold red] Erreur : {e}")
        notification.notify(title="Vega - Erreur", message=str(e), app_name="Vega")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Vega : Downloader Universel",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("url", help="Lien de la vidéo (YouTube, TikTok, Instagram, etc.)")
    parser.add_argument("-a", "--audio", action="store_true", help="Télécharger uniquement l'audio (MP3)")
    parser.add_argument("-vo", "--video-only", action="store_true", help="Télécharger la vidéo sans le son")
    parser.add_argument("-q", "--quality", type=str, help="Limiter la résolution (ex: 720, 1080)")
    parser.add_argument("-s", "--start", type=str, help="Début de l'extrait à télécharger (ex: 0:00, 1:23:45)")
    parser.add_argument("-e", "--end", type=str, help="Fin de l'extrait à télécharger (ex: 3:00, 1:25:00)")

    args = parser.parse_args()

    if args.url:
        run_vega(args.url, audio_only=args.audio, video_only=args.video_only, quality=args.quality,
                  start=args.start, end=args.end)
    else:
        # Affichage d'un bel en-tête même pour l'aide
        console.print(Panel.fit("[bold cyan]VEGA[/bold cyan] - Aide", border_style="blue"))
        parser.print_help()
