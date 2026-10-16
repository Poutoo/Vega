# Vega

**[English](README.md) | Français**

[![PyPI](https://img.shields.io/pypi/v/vega-dlp?color=F48FB1)](https://pypi.org/project/vega-dlp/)
[![License: MIT](https://img.shields.io/github/license/Poutoo/Vega?color=F48FB1)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-F48FB1)](https://www.python.org/)
[![Built with yt-dlp](https://img.shields.io/badge/built%20with-yt--dlp-F48FB1)](https://github.com/yt-dlp/yt-dlp)

Utilitaire CLI universel pour télécharger des vidéos (YouTube, TikTok, Instagram, etc.) via [`yt-dlp`](https://github.com/yt-dlp/yt-dlp), avec une interface moderne basée sur `rich`.

## Prérequis

- [Python 3.9+](https://www.python.org/downloads/)
- [FFmpeg](https://ffmpeg.org/) installé et accessible dans le PATH (nécessaire pour fusionner l'audio/vidéo et pour les conversions)

## Installation

Le moyen le plus simple d'obtenir la commande `vega` disponible partout sur votre système, sans se soucier des environnements virtuels, est [`pipx`](https://pipx.pypa.io/) :

```bash
# Installer pipx une fois, si vous ne l'avez pas déjà
python -m pip install --user pipx
python -m pipx ensurepath

# Installer Vega
pipx install vega-dlp
```

Redémarrez votre terminal, puis lancez `vega --help` pour confirmer l'installation.

<details>
<summary>Alternative : pip classique</summary>

```bash
pip install vega-dlp
```

</details>

<details>
<summary>Alternative : exécuter depuis les sources (pour les contributeurs)</summary>

```bash
git clone https://github.com/Poutoo/Vega.git
cd Vega

python -m venv venv
venv\Scripts\Activate.ps1   # PowerShell
# ou : venv\Scripts\activate.bat   # CMD

pip install -e .
```

</details>

## Utilisation

```bash
vega <url> [options]
```

Vous préférez un navigateur au terminal ? Vega propose aussi une interface web locale — voir [Interface web](#interface-web) ci-dessous.

## Commandes et options

| Commande / Option | Alias court | Description |
|---|---|---|
| `<url>` | — | (Obligatoire) Lien de la vidéo à télécharger (YouTube, TikTok, Instagram, etc.) |
| `--audio` | `-a` | Télécharge uniquement l'audio, converti en MP3 (qualité 192 kbps) |
| `--video-only` | `-vo` | Télécharge uniquement la vidéo, sans le son |
| `--quality <valeur>` | `-q <valeur>` | Limite la résolution vidéo (ex : `720`, `1080`) |
| `--start <temps>` | `-s <temps>` | Début de l'extrait à télécharger (ex : `0:00`, `1:23:45`) |
| `--end <temps>` | `-e <temps>` | Fin de l'extrait à télécharger (ex : `3:00`, `1:25:00`) |
| `--help` | `-h` | Affiche l'aide du programme |
| `web` | — | Lance l'interface web locale |

## Exemples

```bash
# Téléchargement simple (meilleure qualité, vidéo + audio)
vega https://www.youtube.com/watch?v=XXXXXXXXXXX

# Téléchargement audio uniquement (MP3)
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -a

# Téléchargement vidéo sans son
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -vo

# Limiter la résolution à 720p
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -q 720

# Combiner les options : vidéo sans son, limitée à 1080p
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -vo -q 1080

# Ne télécharger que l'extrait de 0:00 à 3:00
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -s 0:00 -e 3:00

# Extrait audio uniquement, de 1:23:45 à la fin de la vidéo
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -a -s 1:23:45

# Afficher l'aide
vega --help
```

> **Note :** le découpage utilise `--force-keyframes-at-cuts` en interne pour une coupe précise à la seconde près, ce qui implique un léger ré-encodage local (via FFmpeg) et donc un temps de traitement un peu plus long qu'un téléchargement classique.

## Interface web

Pour celles et ceux qui ne sont pas à l'aise avec un terminal, Vega propose aussi une interface web locale avec les mêmes options de téléchargement et un suivi de la progression en direct. C'est une dépendance optionnelle, exclue de l'installation par défaut pour garder le CLI de base léger.

```bash
# pipx
pipx install "vega-dlp[web]"

# ou pip classique
pip install "vega-dlp[web]"
```

```bash
vega web
```

Cela démarre un serveur accessible uniquement en local (`127.0.0.1`, jamais exposé sur votre réseau) et l'ouvre dans votre navigateur par défaut. Options :

| Option | Description |
|---|---|
| `--port <n>` | Port à utiliser (défaut : `8756`) |
| `--no-browser` | N'ouvre pas automatiquement le navigateur |

## Fonctionnement

- Les vidéos sont automatiquement triées dans le dossier `Téléchargements/<Plateforme>` de l'utilisateur (ex : `Downloads/Youtube/`).
- Chaque téléchargement est enregistré dans `~/.vega/history.json` (titre, URL, plateforme, chemin, date). Ce fichier reste local.
- Une notification système s'affiche à la fin du téléchargement (succès ou erreur).

## Licence

Distribué sous licence [MIT](LICENSE).
