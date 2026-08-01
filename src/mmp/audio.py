"""Offline audio probing and synthesis, built on ffmpeg/ffprobe (no deps)."""

import json
import re
import shutil
import subprocess


def _ffprobe(path):
    if shutil.which("ffprobe"):
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", path],
                capture_output=True, text=True, timeout=30,
            )
            if out.returncode == 0 and out.stdout.strip():
                return json.loads(out.stdout)
        except Exception:
            pass
    return None


def probe(path):
    """Return a dict of metadata for a media file. Never raises."""
    data = _ffprobe(path)
    if data:
        fmt = data.get("format", {})
        streams = data.get("streams", [])
        aud = [s for s in streams if s.get("codec_type") == "audio"]
        return {
            "ok": True,
            "path": path,
            "container": fmt.get("format_name"),
            "duration_s": _to_float(fmt.get("duration")),
            "bitrate_bps": _to_float(fmt.get("bit_rate")),
            "size_bytes": _to_float(fmt.get("size")),
            "streams": [
                {
                    "type": s.get("codec_type"),
                    "codec": s.get("codec_name"),
                    "sample_rate_hz": _to_float(s.get("sample_rate")),
                    "channels": _to_int(s.get("channels")),
                }
                for s in streams
            ],
            "audio_stream_count": len(aud),
        }

    # Fallback: parse `ffmpeg -i` stderr.
    if shutil.which("ffmpeg"):
        try:
            out = subprocess.run(
                ["ffmpeg", "-hide_banner", "-i", path],
                capture_output=True, text=True, timeout=30,
            )
            txt = out.stderr
            m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", txt)
            dur = ":".join(m.groups()) if m else None
            return {
                "ok": True,
                "path": path,
                "duration": dur,
                "note": "parsed from ffmpeg -i (ffprobe unavailable)",
                "excerpt": txt[:600].strip(),
            }
        except Exception as e:  # pragma: no cover
            return {"ok": False, "path": path, "error": str(e)}

    return {"ok": False, "path": path, "error": "ffmpeg/ffprobe not found"}


def synth_tone(out_path, seconds=2.0, freq=440.0):
    """Synthesize a PCM test tone with ffmpeg. Returns True on success."""
    if not shutil.which("ffmpeg"):
        return False
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"sine=frequency={freq}:duration={seconds}",
        "-c:a", "pcm_s16le", out_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r.returncode == 0


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
