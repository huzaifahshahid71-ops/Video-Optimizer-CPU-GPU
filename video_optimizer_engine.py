from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "VideoOptimizerStudio"
FFMPEG_DIR = APP_DIR / "ffmpeg"
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


@dataclass
class VideoInfo:
    path: Path
    width: int = 0
    height: int = 0
    fps: float = 0.0
    duration: float = 0.0
    codec: str = "unknown"
    bitrate: int = 0
    pix_fmt: str = "unknown"
    size_bytes: int = 0

    @property
    def resolution(self) -> str:
        return f"{self.width}×{self.height}" if self.width and self.height else "Unknown"

    @property
    def fps_text(self) -> str:
        if not self.fps:
            return "Unknown"
        return f"{self.fps:.3f}".rstrip("0").rstrip(".")

    @property
    def size_text(self) -> str:
        n = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024 or unit == "TB":
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"


@dataclass
class EncoderSettings:
    mode: str = "CPU"  # CPU | GPU | Auto
    cpu_preset: str = "medium"
    cpu_crf: int = 20
    gpu_preset: str = "p5"
    gpu_cq: int = 20
    audio_bitrate: str = "192k"
    overwrite: bool = True
    suffix: str = "_optimized"


def _rate_to_float(value: str | None) -> float:
    if not value or value in {"0/0", "N/A"}:
        return 0.0
    try:
        if "/" in value:
            a, b = value.split("/", 1)
            bval = float(b)
            return float(a) / bval if bval else 0.0
        return float(value)
    except Exception:
        return 0.0


def _candidate_bins() -> list[Path]:
    candidates: list[Path] = []
    if getattr(sys, "_MEIPASS", None):
        candidates.append(Path(sys._MEIPASS))
    candidates.extend([
        FFMPEG_DIR,
        Path(r"C:\ffmpeg\bin"),
        Path(r"C:\Program Files\ffmpeg\bin"),
        Path(r"C:\Program Files (x86)\ffmpeg\bin"),
    ])
    return candidates


def find_executable(name: str) -> Optional[str]:
    direct = shutil.which(name)
    if direct:
        return direct
    for folder in _candidate_bins():
        p = folder / name
        if p.exists():
            return str(p)
    return None


def find_ffmpeg_pair() -> tuple[Optional[str], Optional[str]]:
    ffmpeg = find_executable("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    ffprobe = find_executable("ffprobe.exe" if os.name == "nt" else "ffprobe")
    return ffmpeg, ffprobe


def install_ffmpeg(
    progress_cb: Optional[Callable[[float, str], None]] = None,
    url: str = FFMPEG_DOWNLOAD_URL,
) -> tuple[str, str]:
    """Download and install a Windows FFmpeg essentials build into LocalAppData."""
    if os.name != "nt":
        raise RuntimeError("Automatic FFmpeg installation is currently supported on Windows only.")

    APP_DIR.mkdir(parents=True, exist_ok=True)
    FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
    archive = APP_DIR / "ffmpeg-release-essentials.zip"

    def report(value: float, text: str) -> None:
        if progress_cb:
            progress_cb(max(0.0, min(1.0, value)), text)

    report(0.0, "Connecting to FFmpeg download...")
    req = urllib.request.Request(url, headers={"User-Agent": "VideoOptimizerStudio/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response, open(archive, "wb") as out:
        total = int(response.headers.get("Content-Length", "0") or 0)
        downloaded = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            if total:
                report(min(0.80, (downloaded / total) * 0.80), f"Downloading FFmpeg… {downloaded / 1024 / 1024:.0f} MB")

    report(0.82, "Extracting FFmpeg…")
    found = {}
    with zipfile.ZipFile(archive, "r") as zf:
        names = zf.namelist()
        for binary in ("ffmpeg.exe", "ffprobe.exe"):
            match = next((n for n in names if n.lower().endswith("/bin/" + binary)), None)
            if not match:
                raise RuntimeError(f"{binary} was not found in the downloaded archive.")
            target = FFMPEG_DIR / binary
            with zf.open(match) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            found[binary] = str(target)

    try:
        archive.unlink(missing_ok=True)
    except Exception:
        pass

    report(1.0, "FFmpeg installed.")
    return found["ffmpeg.exe"], found["ffprobe.exe"]


def probe_video(path: str | Path, ffprobe: Optional[str] = None) -> VideoInfo:
    path = Path(path)
    _, ffprobe_found = find_ffmpeg_pair()
    ffprobe = ffprobe or ffprobe_found
    if not ffprobe:
        raise RuntimeError("FFprobe was not found.")

    cmd = [
        ffprobe, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=codec_name,width,height,r_frame_rate,avg_frame_rate,bit_rate,pix_fmt:"
        "format=duration,bit_rate",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, creationflags=_no_window_flags())
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "FFprobe failed.")

    data = json.loads(result.stdout or "{}")
    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}
    fps = _rate_to_float(stream.get("avg_frame_rate") or stream.get("r_frame_rate"))
    duration = float(fmt.get("duration") or 0.0)
    bitrate = int(stream.get("bit_rate") or fmt.get("bit_rate") or 0)
    return VideoInfo(
        path=path,
        width=int(stream.get("width") or 0),
        height=int(stream.get("height") or 0),
        fps=fps,
        duration=duration,
        codec=str(stream.get("codec_name") or "unknown"),
        bitrate=bitrate,
        pix_fmt=str(stream.get("pix_fmt") or "unknown"),
        size_bytes=path.stat().st_size if path.exists() else 0,
    )


def ffmpeg_supports_nvenc(ffmpeg: Optional[str] = None) -> bool:
    """Check FFmpeg build support for HEVC NVENC without initializing the GPU."""
    ffmpeg_found, _ = find_ffmpeg_pair()
    ffmpeg = ffmpeg or ffmpeg_found
    if not ffmpeg:
        return False
    try:
        listed = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=15,
            creationflags=_no_window_flags(),
        )
        return listed.returncode == 0 and "hevc_nvenc" in listed.stdout
    except Exception:
        return False


def has_nvenc(ffmpeg: Optional[str] = None) -> bool:
    """Return True only when HEVC NVENC can actually initialize on this machine."""
    ffmpeg_found, _ = find_ffmpeg_pair()
    ffmpeg = ffmpeg or ffmpeg_found
    if not ffmpeg or not ffmpeg_supports_nvenc(ffmpeg):
        return False
    try:
        # A build may list NVENC even when no compatible NVIDIA GPU/driver exists.
        # Initialize a one-frame encode only when GPU/Auto is explicitly requested.
        test = subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=c=black:s=64x64:r=1",
                "-frames:v", "1",
                "-c:v", "hevc_nvenc",
                "-f", "null", "-",
            ],
            capture_output=True, text=True, timeout=20,
            creationflags=_no_window_flags(),
        )
        return test.returncode == 0
    except Exception:
        return False


def resolve_mode(requested_mode: str, nvenc_available: bool) -> str:
    mode = requested_mode.strip().upper()
    if mode == "CPU":
        return "CPU"
    if mode == "GPU":
        if not nvenc_available:
            raise RuntimeError(
                "GPU mode was selected, but NVIDIA HEVC NVENC is not available.\n\n"
                "Choose CPU/Auto, install an NVIDIA driver, or use an FFmpeg build with NVENC support."
            )
        return "GPU"
    if mode == "AUTO":
        return "GPU" if nvenc_available else "CPU"
    raise ValueError(f"Unknown encoder mode: {requested_mode}")


def build_ffmpeg_command(
    source: str | Path,
    output: str | Path,
    settings: EncoderSettings,
    *,
    ffmpeg: Optional[str] = None,
    nvenc_available: Optional[bool] = None,
) -> tuple[list[str], str]:
    ffmpeg_found, _ = find_ffmpeg_pair()
    ffmpeg = ffmpeg or ffmpeg_found or "ffmpeg"
    if nvenc_available is None:
        nvenc_available = has_nvenc(ffmpeg)
    actual_mode = resolve_mode(settings.mode, nvenc_available)

    if actual_mode == "GPU":
        video_options = [
            "-c:v", "hevc_nvenc",
            "-preset", settings.gpu_preset,
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", str(settings.gpu_cq),
            "-b:v", "0",
            "-pix_fmt", "yuv420p",
            "-tag:v", "hvc1",
        ]
    else:
        video_options = [
            "-c:v", "libx265",
            "-preset", settings.cpu_preset,
            "-crf", str(settings.cpu_crf),
            "-threads", "0",
            "-pix_fmt", "yuv420p",
            "-tag:v", "hvc1",
        ]

    cmd = [
        ffmpeg,
        "-hide_banner",
        "-y" if settings.overwrite else "-n",
        "-i", str(source),
        "-map", "0:v:0",
        "-map", "0:a?",
        *video_options,
        "-c:a", "aac",
        "-b:a", settings.audio_bitrate,
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        "-nostats",
        str(output),
    ]
    return cmd, actual_mode


def output_path_for(source: str | Path, output_dir: str | Path, suffix: str) -> Path:
    source = Path(source)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{source.stem}{suffix}.mp4"


class EncodingCancelled(RuntimeError):
    pass


def encode_video(
    source: str | Path,
    output: str | Path,
    info: VideoInfo,
    settings: EncoderSettings,
    *,
    ffmpeg: Optional[str] = None,
    nvenc_available: Optional[bool] = None,
    progress_cb: Optional[Callable[[float, str, str], None]] = None,
    cancel_event: Optional[threading.Event] = None,
) -> str:
    cmd, actual_mode = build_ffmpeg_command(
        source, output, settings, ffmpeg=ffmpeg, nvenc_available=nvenc_available
    )
    kwargs = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=_no_window_flags(),
    )
    process = subprocess.Popen(cmd, **kwargs)
    last_speed = "?"
    last_time = 0.0

    try:
        assert process.stdout is not None
        for raw in process.stdout:
            if cancel_event and cancel_event.is_set():
                process.terminate()
                try:
                    process.wait(timeout=3)
                except Exception:
                    process.kill()
                raise EncodingCancelled("Encoding cancelled.")

            line = raw.strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)

            if key == "speed":
                last_speed = value
            elif key in {"out_time", "out_time_us", "out_time_ms"}:
                if key == "out_time":
                    last_time = _timecode_seconds(value)
                else:
                    try:
                        # FFmpeg currently reports out_time_us in microseconds.
                        last_time = float(value) / 1_000_000.0
                    except Exception:
                        pass
                pct = min(1.0, last_time / info.duration) if info.duration > 0 else 0.0
                if progress_cb:
                    progress_cb(pct, last_speed, actual_mode)
            elif key == "progress" and value == "end":
                if progress_cb:
                    progress_cb(1.0, last_speed, actual_mode)

        process.wait()
    finally:
        try:
            if process.stdout:
                process.stdout.close()
        except Exception:
            pass

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg exited with code {process.returncode}.")
    return actual_mode


def _timecode_seconds(value: str) -> float:
    try:
        h, m, s = value.split(":")
        return float(h) * 3600 + float(m) * 60 + float(s)
    except Exception:
        return 0.0


def _no_window_flags() -> int:
    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0
