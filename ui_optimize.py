from __future__ import annotations
from tkinter import ttk
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

class OptimizePageMixin:
    def _build_optimize_page(self):
        page = ctk.CTkFrame(self.host, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(3, weight=1)
        head = self._header(
            page, "Optimize",
            "Keep the original resolution and frame rate while recompressing to iPhone-friendly HEVC."
        )
        self.start_btn = ctk.CTkButton(
            head, text="Start Optimization", width=165, height=40,
            font=ctk.CTkFont(weight="bold"), command=self.start_encoding
        )
        self.start_btn.grid(row=0, column=1, rowspan=2, padx=(10, 0), sticky="e")

        toolbar = ctk.CTkFrame(page, corner_radius=14)
        toolbar.grid(row=1, column=0, padx=26, pady=(0, 10), sticky="ew")
        ctk.CTkButton(toolbar, text="Add Videos", command=self.add_videos).pack(side="left", padx=(12, 5), pady=11)
        ctk.CTkButton(toolbar, text="Add Folder", fg_color="transparent", border_width=1, command=self.add_folder).pack(side="left", padx=5, pady=11)
        ctk.CTkButton(toolbar, text="Remove", fg_color="transparent", border_width=1, command=self.remove_selected).pack(side="left", padx=5, pady=11)
        ctk.CTkButton(toolbar, text="Clear", fg_color="transparent", border_width=1, command=self.clear_videos).pack(side="left", padx=5, pady=11)
        self.cancel_btn = ctk.CTkButton(
            toolbar, text="Cancel", fg_color="#B91C1C", hover_color="#991B1B",
            command=self.cancel_encoding, state="disabled"
        )
        self.cancel_btn.pack(side="right", padx=12, pady=11)

        cards = ctk.CTkFrame(page, fg_color="transparent")
        cards.grid(row=2, column=0, padx=26, pady=(0, 10), sticky="ew")
        cards.grid_columnconfigure((0,1,2), weight=1)
        self._metric(cards, 0, "Queue", self.queue_text)
        self._metric(cards, 1, "Encoder", self.encoder_mode)
        self._metric(cards, 2, "Environment", self.encoder_status)

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=3, column=0, padx=26, pady=(0, 10), sticky="nsew")
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        queue = ctk.CTkFrame(body, corner_radius=14)
        queue.grid(row=0, column=0, padx=(0,7), sticky="nsew")
        queue.grid_rowconfigure(1, weight=1)
        queue.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(queue, text="Video queue", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=15, pady=(13,8), sticky="w"
        )

        wrap = ctk.CTkFrame(queue, fg_color="transparent")
        wrap.grid(row=1, column=0, padx=12, pady=(0,12), sticky="nsew")
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        columns = ("name", "resolution", "fps", "codec", "size")
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings", style="Video.Treeview")
        for col, text, width in [
            ("name","File",360),("resolution","Resolution",110),("fps","FPS",85),("codec","Codec",90),("size","Size",90)
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w" if col == "name" else "center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ctk.CTkScrollbar(wrap, command=self.tree.yview)
        scroll.grid(row=0, column=1, padx=(5,0), sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self._configure_tree_style()

        settings = ctk.CTkScrollableFrame(body, corner_radius=14, label_text="Quick Settings")
        settings.grid(row=0, column=1, padx=(7,0), sticky="nsew")

        ctk.CTkLabel(settings, text="Encoding mode", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(2,3))
        ctk.CTkLabel(
            settings,
            text="CPU = best compression/control. GPU = fastest. Auto uses GPU when NVENC is available.",
            wraplength=360, justify="left", text_color=("gray38","gray66")
        ).pack(anchor="w", pady=(0,10))
        mode_seg = ctk.CTkSegmentedButton(
            settings, values=["CPU", "GPU", "Auto"], variable=self.encoder_mode,
            command=lambda _v: self._update_mode_description()
        )
        mode_seg.pack(fill="x", pady=(0,14))

        self.mode_description = ctk.CTkLabel(settings, text="", wraplength=360, justify="left")
        self.mode_description.pack(anchor="w", pady=(0,14))
        self._update_mode_description()

        ctk.CTkLabel(settings, text="Output folder", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        outrow = ctk.CTkFrame(settings, fg_color="transparent")
        outrow.pack(fill="x", pady=(5,12))
        ctk.CTkEntry(outrow, textvariable=self.output_folder).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(outrow, text="Browse", width=72, command=self.pick_output_folder).pack(side="left", padx=(7,0))

        ctk.CTkLabel(settings, text="Output suffix", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkEntry(settings, textvariable=self.output_suffix).pack(fill="x", pady=(5,12))
        ctk.CTkSwitch(settings, text="Overwrite existing output", variable=self.overwrite).pack(anchor="w", pady=(0,14))

        ctk.CTkFrame(settings, height=1, fg_color=("gray82","gray25")).pack(fill="x", pady=(0,14))
        ctk.CTkLabel(
            settings,
            text="Preservation policy",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            settings,
            text="✓ Original width & height\n✓ Original frame timing / FPS\n✓ HEVC Main-compatible yuv420p\n✓ hvc1 tag for Apple compatibility\n✓ AAC audio + fast-start MP4",
            justify="left", text_color=("gray34","gray72")
        ).pack(anchor="w", pady=(6,14))

        progress = ctk.CTkFrame(page, corner_radius=14)
        progress.grid(row=4, column=0, padx=26, pady=(0,20), sticky="ew")
        progress.grid_columnconfigure(0, weight=1)
        statusrow = ctk.CTkFrame(progress, fg_color="transparent")
        statusrow.grid(row=0,column=0,padx=14,pady=(10,4),sticky="ew")
        statusrow.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(statusrow,textvariable=self.status_text,anchor="w").grid(row=0,column=0,sticky="ew")
        ctk.CTkLabel(statusrow,textvariable=self.progress_text).grid(row=0,column=1,sticky="e")
        self.progress = ctk.CTkProgressBar(progress)
        self.progress.set(0)
        self.progress.grid(row=1,column=0,padx=14,pady=(2,7),sticky="ew")
        ctk.CTkLabel(progress,textvariable=self.detail_text,text_color=("gray40","gray64"),anchor="w").grid(
            row=2,column=0,padx=14,pady=(0,10),sticky="ew"
        )
        return page
