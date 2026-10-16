import argparse
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from vega.core import run_download
from vega.progress import PINK, PINK_DEEP, PINK_LIGHT, RichProgressSink

console = Console()

DEFAULT_WEB_PORT = 8756


def print_banner() -> None:
    console.print(Panel.fit(
        f"[bold {PINK_DEEP}]VEGA[/] [white]v1.2 - Downloader Universel[/white]",
        border_style=PINK
    ))


def print_help() -> None:
    """Renders styled help instead of argparse's default output."""
    print_banner()

    console.print(f"\n[bold {PINK_DEEP}]Usage :[/] [{PINK}]vega <url> \\[options][/]")
    console.print(f"[bold {PINK_DEEP}]       [/] [{PINK}]vega web \\[--port <n>] \\[--no-browser][/]\n")

    table = Table(show_header=True, header_style=f"bold {PINK_DEEP}", border_style=PINK)
    table.add_column("Option", style=f"bold {PINK_DEEP}")
    table.add_column("Alias", style=PINK)
    table.add_column("Description")

    table.add_row("url", "—", "Lien de la vidéo à télécharger (YouTube, TikTok, Instagram, etc.)")
    table.add_row("--audio", "-a", "Télécharger uniquement l'audio (MP3)")
    table.add_row("--video-only", "-vo", "Télécharger la vidéo sans le son")
    table.add_row("--quality <val>", "-q <val>", "Limiter la résolution (ex: 720, 1080)")
    table.add_row("--start <temps>", "-s <temps>", "Début de l'extrait (ex: 0:00, 1:23:45)")
    table.add_row("--end <temps>", "-e <temps>", "Fin de l'extrait (ex: 3:00, 1:25:00)")
    table.add_row("--output <dossier>", "-o <dossier>", "Dossier de destination (défaut : Downloads/<Plateforme>)")
    table.add_row("--cookies-from-browser <nav>", "—", "Utiliser les cookies d'un navigateur (ex: firefox, chrome)")
    table.add_row("--help", "-h", "Affiche cette aide")
    table.add_row("web", "—", "Lance l'interface web locale")

    console.print(table)

    console.print(f"\n[bold {PINK_DEEP}]Exemples :[/]")
    console.print(f"  [{PINK_LIGHT}]$[/] vega https://youtu.be/XXXX -a")
    console.print(f"  [{PINK_LIGHT}]$[/] vega https://youtu.be/XXXX -vo -q 720")
    console.print(f"  [{PINK_LIGHT}]$[/] vega https://youtu.be/XXXX -s 0:00 -e 3:00")
    console.print(f"  [{PINK_LIGHT}]$[/] vega web\n")


class RichHelpAction(argparse.Action):
    """argparse Action that renders styled help instead of the default output."""
    def __init__(self, option_strings, dest, **kwargs):
        kwargs.setdefault("nargs", 0)
        kwargs.setdefault("help", "Affiche cette aide")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print_help()
        parser.exit()


def run_cli_download(url: str, audio_only: bool, video_only: bool, quality: Optional[str],
                      start: Optional[str], end: Optional[str], output_dir: Optional[Path],
                      cookies_from_browser: Optional[str]) -> bool:
    print_banner()
    sink = RichProgressSink(console)
    with sink.progress:
        return run_download(url, sink, audio_only=audio_only, video_only=video_only,
                     quality=quality, start=start, end=end, output_dir=output_dir,
                     cookies_from_browser=cookies_from_browser)


def parse_web_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="vega web", description="Lance l'interface web locale de Vega")
    parser.add_argument("--port", type=int, default=DEFAULT_WEB_PORT,
                         help=f"Port local à utiliser (défaut : {DEFAULT_WEB_PORT})")
    parser.add_argument("--no-browser", action="store_true",
                         help="Ne pas ouvrir automatiquement le navigateur")
    return parser.parse_args(argv)


def launch_web(port: int, open_browser: bool) -> None:
    """Binds to 127.0.0.1 only — never exposed beyond the local machine."""
    try:
        import uvicorn
    except ImportError:
        console.print(
            f"[bold red]✘[/bold red] L'interface web nécessite des dépendances supplémentaires.\n"
            f"Installe-les avec : [bold {PINK_DEEP}]pip install vega-dlp\\[web][/]"
        )
        return

    from vega.web.app import create_app

    print_banner()
    console.print(f"[bold {PINK_DEEP}][+][/] Interface web sur [{PINK}]http://127.0.0.1:{port}[/]")
    console.print(f"[{PINK_LIGHT}]  (Ctrl+C pour arrêter)[/]\n")

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        args = parse_web_args(sys.argv[2:])
        launch_web(port=args.port, open_browser=not args.no_browser)
        return

    parser = argparse.ArgumentParser(description="Vega : Downloader Universel", add_help=False)
    parser.add_argument("-h", "--help", action=RichHelpAction)
    parser.add_argument("url", help="Lien de la vidéo (YouTube, TikTok, Instagram, etc.)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("-a", "--audio", action="store_true", help="Télécharger uniquement l'audio (MP3)")
    mode.add_argument("-vo", "--video-only", action="store_true", help="Télécharger la vidéo sans le son")
    parser.add_argument("-q", "--quality", type=str, help="Limiter la résolution (ex: 720, 1080)")
    parser.add_argument("-s", "--start", type=str, help="Début de l'extrait à télécharger (ex: 0:00, 1:23:45)")
    parser.add_argument("-e", "--end", type=str, help="Fin de l'extrait à télécharger (ex: 3:00, 1:25:00)")

    parser.add_argument("-o", "--output", type=Path, help="Dossier de destination (défaut : ~/Downloads/<Plateforme>)")

    parser.add_argument("--cookies-from-browser", metavar="NAVIGATEUR",
                         help="Utiliser les cookies d'un navigateur (ex: firefox, chrome) pour les contenus protégés")

    args = parser.parse_args()
    ok = run_cli_download(args.url, audio_only=args.audio, video_only=args.video_only, quality=args.quality,
                           start=args.start, end=args.end, output_dir=args.output,
                           cookies_from_browser=args.cookies_from_browser)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
