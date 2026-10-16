from pathlib import Path

import pytest

from vega.core import build_ydl_opts, parse_time, validate_options


def noop(_):
    pass


@pytest.mark.parametrize("value,expected", [
    ("45", 45.0),
    ("1:30", 90.0),
    ("1:02:03", 3723.0),
    ("0:00", 0.0),
])
def test_parse_time_valid(value, expected):
    assert parse_time(value) == expected


@pytest.mark.parametrize("value", ["abc", "1:2:3:4", "-5", "1:-5", "", "nan", "inf"])
def test_parse_time_invalid(value):
    with pytest.raises(ValueError):
        parse_time(value)


def valid(**overrides):
    kwargs = dict(audio_only=False, video_only=False, quality=None, start=None, end=None)
    kwargs.update(overrides)
    return kwargs


def test_validate_accepts_defaults_and_full_options():
    validate_options(**valid())
    validate_options(**valid(quality="720", start="0:10", end="1:00"))


@pytest.mark.parametrize("overrides", [
    dict(audio_only=True, video_only=True),
    dict(quality="72x"),
    dict(quality="720]; x"),
    dict(start="abc"),
    dict(start="5:00", end="1:00"),
    dict(start="1:00", end="1:00"),
])
def test_validate_rejects(overrides):
    with pytest.raises(ValueError):
        validate_options(**valid(**overrides))


def opts(**overrides):
    kwargs = dict(audio_only=False, video_only=False, quality=None, start=None, end=None)
    kwargs.update(overrides)
    return build_ydl_opts(Path("out"), noop, **kwargs)


def test_default_format_is_best_video_plus_audio():
    assert opts()["format"] == "bestvideo+bestaudio/best"


def test_quality_caps_height():
    assert "[height<=?720]" in opts(quality="720")["format"]


def test_audio_only_extracts_mp3():
    o = opts(audio_only=True)
    assert o["format"] == "bestaudio/best"
    assert o["postprocessors"][0]["preferredcodec"] == "mp3"


def test_video_only_strips_audio():
    o = opts(video_only=True)
    assert "acodec=none" in o["format"]
    assert o["postprocessor_args"]["merger"] == ["-an"]


def test_clip_sets_ranges_and_keyframes():
    o = opts(start="0:10", end="0:20")
    assert "download_ranges" in o
    assert o["force_keyframes_at_cuts"] is True


def test_no_clip_by_default():
    assert "download_ranges" not in opts()


def test_run_download_fails_fast_without_ffmpeg(monkeypatch):
    import vega.core as core

    errors = []

    class Sink:
        def on_error(self, message):
            errors.append(message)

        def on_analyzing(self):
            raise AssertionError("must not start analysing without FFmpeg")

    monkeypatch.setattr(core.shutil, "which", lambda _: None)
    assert core.run_download("https://example.com/v", Sink()) is False
    assert "FFmpeg" in errors[0]
