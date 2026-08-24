# Vega

**English | [Français](README.fr.md)**

[![License: MIT](https://img.shields.io/github/license/Poutoo/Vega?color=F48FB1)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-F48FB1)](https://www.python.org/)
[![Built with yt-dlp](https://img.shields.io/badge/built%20with-yt--dlp-F48FB1)](https://github.com/yt-dlp/yt-dlp)

Universal CLI utility to download videos (YouTube, TikTok, Instagram, etc.) via [`yt-dlp`](https://github.com/yt-dlp/yt-dlp), with a modern interface powered by `rich`.

## Requirements

- [Python 3.9+](https://www.python.org/downloads/)
- [FFmpeg](https://ffmpeg.org/) installed and available in your PATH (needed to merge audio/video and for conversions)

## Installation

The simplest way to get the `vega` command available everywhere on your system, without worrying about virtual environments, is [`pipx`](https://pipx.pypa.io/):

```bash
# Install pipx once, if you don't have it yet
python -m pip install --user pipx
python -m pipx ensurepath

# Install Vega
pipx install git+https://github.com/Poutoo/Vega.git
```

Restart your terminal, then run `vega --help` to confirm it's installed.

<details>
<summary>Alternative: plain pip</summary>

```bash
pip install git+https://github.com/Poutoo/Vega.git
```

</details>

<details>
<summary>Alternative: run from source (for contributors)</summary>

```bash
git clone https://github.com/Poutoo/Vega.git
cd Vega

python -m venv venv
venv\Scripts\Activate.ps1   # PowerShell
# or: venv\Scripts\activate.bat   # CMD

pip install -e .
```

</details>

## Usage

```bash
vega <url> [options]
```

## Commands and options

| Command / Option | Short alias | Description |
|---|---|---|
| `<url>` | — | (Required) Link to the video to download (YouTube, TikTok, Instagram, etc.) |
| `--audio` | `-a` | Download audio only, converted to MP3 (192 kbps) |
| `--video-only` | `-vo` | Download video only, without sound |
| `--quality <value>` | `-q <value>` | Limit video resolution (e.g. `720`, `1080`) |
| `--start <time>` | `-s <time>` | Start of the clip to download (e.g. `0:00`, `1:23:45`) |
| `--end <time>` | `-e <time>` | End of the clip to download (e.g. `3:00`, `1:25:00`) |
| `--help` | `-h` | Show the program's help message |

## Examples

```bash
# Simple download (best quality, video + audio)
vega https://www.youtube.com/watch?v=XXXXXXXXXXX

# Audio only download (MP3)
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -a

# Video only, no sound
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -vo

# Limit resolution to 720p
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -q 720

# Combine options: video only, capped at 1080p
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -vo -q 1080

# Download only the 0:00-3:00 clip
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -s 0:00 -e 3:00

# Audio-only clip, from 1:23:45 to the end of the video
vega https://www.youtube.com/watch?v=XXXXXXXXXXX -a -s 1:23:45

# Show help
vega --help
```

> **Note:** clipping uses `--force-keyframes-at-cuts` internally for a frame-accurate cut, which requires a light local re-encode (via FFmpeg) and therefore takes a bit longer than a regular download.

## How it works

- Videos are automatically sorted into the user's `Downloads/<Platform>` folder (e.g. `Downloads/Youtube/`).
- Every download is logged to `history.json` (title, URL, platform, path, date). This file stays local and is not versioned.
- A system notification is shown when the download finishes (success or error).

## License

Distributed under the [MIT license](LICENSE).
