from __future__ import annotations

import multiprocessing
import sys
import threading
from pathlib import Path
from typing import Optional
import tkinter as tk

try:
    import customtkinter as ctk
except ImportError as exc:
    raise SystemExit("CustomTkinter is required. Run BUILD_APP.bat.") from exc

from video_optimizer_engine import VideoInfo
from ui_shell import UIShellMixin
from ui_optimize import OptimizePageMixin
from ui_settings import SettingsPagesMixin
from app_actions import ActionsMixin

APP_TITLE = "Video Optimizer Studio"
APP_VERSION = "1.0"
APP_USER_MODEL_ID = "VideoOptimizerStudio.Windows.1.0"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")


def resource_path(name: str) -> Optional[Path]:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    p = root / name
    return p if p.exists() else None


class VideoOptimizerApp(ctk.CTk, UIShellMixin, OptimizePageMixin, SettingsPagesMixin, ActionsMixin):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1460x900")
        self.minsize(1160, 720)
        self.protocol("WM_DELETE_WINDOW", self._close_app)
        self._set_windows_identity()
        self._set_icon()
        self.after(300, self._set_icon)

        self.video_paths: list[Path] = []
        self.video_infos: dict[Path, VideoInfo] = {}
        self.cancel_event = threading.Event()
        self.worker: Optional[threading.Thread] = None
        self.encoding = False

        self.encoder_mode = tk.StringVar(value="CPU")
        self.cpu_crf = tk.IntVar(value=20)
        self.cpu_preset = tk.StringVar(value="medium")
        self.gpu_cq = tk.IntVar(value=20)
        self.gpu_preset = tk.StringVar(value="p5")
        self.audio_bitrate = tk.StringVar(value="192k")
        self.output_folder = tk.StringVar(value=str(Path.home() / "Videos"))
        self.output_suffix = tk.StringVar(value="_optimized")
        self.overwrite = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Add a video to begin.")
        self.detail_text = tk.StringVar(value="Resolution and frame rate are preserved by default.")
        self.encoder_status = tk.StringVar(value="Checking FFmpeg…")
        self.progress_text = tk.StringVar(value="0%")
        self.queue_text = tk.StringVar(value="0 videos")

        self._build_ui()
        self.after(50, self.refresh_environment)

    def _set_windows_identity(self) -> None:
        if not sys.platform.startswith("win"):
            return
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except Exception:
            pass

    def _set_icon(self) -> None:
        ico = resource_path("video_optimizer_studio.ico")
        png = resource_path("video_optimizer_studio_icon.png")
        if ico:
            try:
                self.iconbitmap(default=str(ico))
            except Exception:
                pass
        if png:
            try:
                if not hasattr(self, "_icon_photo"):
                    self._icon_photo = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._icon_photo)
            except Exception:
                pass


def main():
    multiprocessing.freeze_support()
    app=VideoOptimizerApp()
    app.mainloop()


if __name__=="__main__":
    main()
