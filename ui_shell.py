from __future__ import annotations
from tkinter import ttk
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

class UIShellMixin:
    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=225, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            sidebar, text="Video\nOptimizer Studio",
            font=ctk.CTkFont(size=28, weight="bold"), justify="left"
        ).grid(row=0, column=0, padx=20, pady=(28, 2), sticky="w")
        ctk.CTkLabel(
            sidebar, text="HEVC optimizer  •  v1.0",
            text_color=("gray40", "gray68"), font=ctk.CTkFont(size=11)
        ).grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        self.pages = {}
        self.nav_buttons = {}
        for row, name in enumerate(["Optimize", "Encoder", "FFmpeg"], start=2):
            btn = ctk.CTkButton(
                sidebar, text=name, anchor="w", height=42, corner_radius=9,
                fg_color="transparent", command=lambda n=name: self.show_page(n)
            )
            btn.grid(row=row, column=0, padx=14, pady=5, sticky="ew")
            self.nav_buttons[name] = btn

        self.appearance = ctk.CTkOptionMenu(
            sidebar, values=["System", "Dark", "Light"],
            command=ctk.set_appearance_mode
        )
        self.appearance.set("System")
        self.appearance.grid(row=8, column=0, padx=14, pady=(8, 18), sticky="ew")

        self.host = ctk.CTkFrame(self, fg_color="transparent")
        self.host.grid(row=0, column=1, sticky="nsew")
        self.host.grid_rowconfigure(0, weight=1)
        self.host.grid_columnconfigure(0, weight=1)

        self.pages["Optimize"] = self._build_optimize_page()
        self.pages["Encoder"] = self._build_encoder_page()
        self.pages["FFmpeg"] = self._build_ffmpeg_page()
        self.show_page("Optimize")

    def show_page(self, name: str) -> None:
        for p in self.pages.values():
            p.grid_remove()
        self.pages[name].grid(row=0, column=0, sticky="nsew")
        for n, b in self.nav_buttons.items():
            b.configure(fg_color=("#3B8ED0", "#1F6AA5") if n == name else "transparent")

    def _header(self, page, title: str, subtitle: str):
        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, padx=26, pady=(22, 12), sticky="ew")
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text=title, font=ctk.CTkFont(size=30, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            head, text=subtitle, text_color=("gray40", "gray66"), font=ctk.CTkFont(size=12)
        ).grid(row=1, column=0, pady=(4, 0), sticky="w")
        return head

    def _metric(self, parent, col, title, var):
        card = ctk.CTkFrame(parent, corner_radius=14)
        card.grid(row=0,column=col,padx=(0 if col==0 else 6, 0 if col==2 else 6),sticky="ew")
        ctk.CTkLabel(card,text=title,text_color=("gray38","gray67")).pack(anchor="w",padx=15,pady=(11,0))
        ctk.CTkLabel(card,textvariable=var,font=ctk.CTkFont(size=19,weight="bold")).pack(anchor="w",padx=15,pady=(0,11))

    def _configure_tree_style(self):
        style=ttk.Style(self)
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("Video.Treeview",background="#1F1F1F",fieldbackground="#1F1F1F",foreground="#E5E7EB",rowheight=34,borderwidth=0,font=("Segoe UI",10))
        style.configure("Video.Treeview.Heading",background="#292929",foreground="#F3F4F6",relief="flat",font=("Segoe UI Semibold",10),padding=(8,8))
        style.map("Video.Treeview",background=[("selected","#1F6AA5")],foreground=[("selected","#FFFFFF")])

    def _update_mode_description(self):
        mode=self.encoder_mode.get()
        text={
            "CPU":"CPU-only: libx265. Best compression efficiency and no NVIDIA encoder usage.",
            "GPU":"GPU-only: NVIDIA HEVC NVENC. The app will stop with an explanation if NVENC is unavailable.",
            "Auto":"Auto: use NVIDIA NVENC when available; otherwise use CPU x265."
        }.get(mode,"")
        self.mode_description.configure(text=text)
