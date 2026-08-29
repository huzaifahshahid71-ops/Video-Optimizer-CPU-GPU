from __future__ import annotations
import tkinter as tk
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

class SettingsPagesMixin:
    def _build_encoder_page(self):
        page = ctk.CTkFrame(self.host, fg_color="transparent")
        page.grid_columnconfigure((0,1),weight=1)
        self._header(page,"Encoder Settings","Tune CPU compression and NVIDIA GPU speed independently.")

        cpu = ctk.CTkFrame(page,corner_radius=14)
        cpu.grid(row=1,column=0,padx=(26,7),pady=(5,22),sticky="nsew")
        gpu = ctk.CTkFrame(page,corner_radius=14)
        gpu.grid(row=1,column=1,padx=(7,26),pady=(5,22),sticky="nsew")

        ctk.CTkLabel(cpu,text="CPU • x265",font=ctk.CTkFont(size=21,weight="bold")).pack(anchor="w",padx=16,pady=(16,3))
        ctk.CTkLabel(
            cpu,text="Best when you want stronger compression, predictable quality, or you deliberately do not want to wake the dGPU.",
            wraplength=460,justify="left",text_color=("gray38","gray66")
        ).pack(anchor="w",padx=16,pady=(0,16))
        ctk.CTkLabel(cpu,text="CRF quality (lower = higher quality)",font=ctk.CTkFont(weight="bold")).pack(anchor="w",padx=16)
        crfrow = ctk.CTkFrame(cpu,fg_color="transparent")
        crfrow.pack(fill="x",padx=16,pady=(6,14))
        crfrow.grid_columnconfigure(0,weight=1)
        self.cpu_crf_slider = ctk.CTkSlider(crfrow,from_=14,to=32,number_of_steps=18,command=lambda v:self.cpu_crf.set(round(v)))
        self.cpu_crf_slider.set(self.cpu_crf.get())
        self.cpu_crf_slider.grid(row=0,column=0,sticky="ew")
        ctk.CTkLabel(crfrow,textvariable=self.cpu_crf,width=42).grid(row=0,column=1,padx=(8,0))
        ctk.CTkLabel(cpu,text="Preset",font=ctk.CTkFont(weight="bold")).pack(anchor="w",padx=16)
        ctk.CTkOptionMenu(
            cpu,values=["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"],
            variable=self.cpu_preset
        ).pack(fill="x",padx=16,pady=(6,16))

        ctk.CTkLabel(gpu,text="GPU • NVIDIA NVENC",font=ctk.CTkFont(size=21,weight="bold")).pack(anchor="w",padx=16,pady=(16,3))
        ctk.CTkLabel(
            gpu,text="Much faster and lower CPU usage. Requires an NVIDIA GPU/driver exposing HEVC NVENC.",
            wraplength=460,justify="left",text_color=("gray38","gray66")
        ).pack(anchor="w",padx=16,pady=(0,16))
        ctk.CTkLabel(gpu,text="CQ quality (lower = higher quality)",font=ctk.CTkFont(weight="bold")).pack(anchor="w",padx=16)
        cqrow = ctk.CTkFrame(gpu,fg_color="transparent")
        cqrow.pack(fill="x",padx=16,pady=(6,14))
        cqrow.grid_columnconfigure(0,weight=1)
        self.gpu_cq_slider = ctk.CTkSlider(cqrow,from_=14,to=32,number_of_steps=18,command=lambda v:self.gpu_cq.set(round(v)))
        self.gpu_cq_slider.set(self.gpu_cq.get())
        self.gpu_cq_slider.grid(row=0,column=0,sticky="ew")
        ctk.CTkLabel(cqrow,textvariable=self.gpu_cq,width=42).grid(row=0,column=1,padx=(8,0))
        ctk.CTkLabel(gpu,text="NVENC preset",font=ctk.CTkFont(weight="bold")).pack(anchor="w",padx=16)
        ctk.CTkOptionMenu(gpu,values=["p1","p2","p3","p4","p5","p6","p7"],variable=self.gpu_preset).pack(
            fill="x",padx=16,pady=(6,16)
        )

        audio = ctk.CTkFrame(page,corner_radius=14)
        audio.grid(row=2,column=0,columnspan=2,padx=26,pady=(0,22),sticky="ew")
        ctk.CTkLabel(audio,text="Audio bitrate",font=ctk.CTkFont(weight="bold")).pack(side="left",padx=(16,10),pady=14)
        ctk.CTkOptionMenu(audio,values=["128k","160k","192k","256k","320k"],variable=self.audio_bitrate,width=120).pack(
            side="left",pady=14
        )
        ctk.CTkLabel(
            audio,text="The original CPU/GPU scripts both used AAC 192 kb/s; that remains the default.",
            text_color=("gray40","gray64")
        ).pack(side="left",padx=14,pady=14)
        return page

    def _build_ffmpeg_page(self):
        page = ctk.CTkFrame(self.host,fg_color="transparent")
        page.grid_columnconfigure(0,weight=1)
        self._header(page,"FFmpeg","Detect or install the encoding backend used by both CPU and GPU modes.")

        card = ctk.CTkFrame(page,corner_radius=14)
        card.grid(row=1,column=0,padx=26,pady=(5,22),sticky="ew")
        ctk.CTkLabel(card,text="Environment status",font=ctk.CTkFont(size=18,weight="bold")).pack(anchor="w",padx=16,pady=(16,3))
        self.ffmpeg_detail = ctk.CTkLabel(card,text="Checking…",justify="left",anchor="w",wraplength=850)
        self.ffmpeg_detail.pack(fill="x",padx=16,pady=(0,14))
        buttons = ctk.CTkFrame(card,fg_color="transparent")
        buttons.pack(fill="x",padx=16,pady=(0,16))
        ctk.CTkButton(buttons,text="Refresh",command=self.refresh_environment).pack(side="left")
        self.install_btn = ctk.CTkButton(
            buttons,text="Install / Update FFmpeg",fg_color="#7C3AED",hover_color="#6D28D9",
            command=self.install_ffmpeg_clicked
        )
        self.install_btn.pack(side="left",padx=8)

        self.install_progress = ctk.CTkProgressBar(card)
        self.install_progress.set(0)
        self.install_progress.pack(fill="x",padx=16,pady=(0,8))
        self.install_text = tk.StringVar(value="")
        ctk.CTkLabel(card,textvariable=self.install_text,text_color=("gray40","gray64")).pack(anchor="w",padx=16,pady=(0,16))

        note = ctk.CTkFrame(page,corner_radius=14)
        note.grid(row=2,column=0,padx=26,pady=(0,22),sticky="ew")
        ctk.CTkLabel(note,text="How it works",font=ctk.CTkFont(size=17,weight="bold")).pack(anchor="w",padx=16,pady=(15,4))
        ctk.CTkLabel(
            note,
            text="The app first uses FFmpeg already available in PATH. If none is found, the installer places ffmpeg.exe and ffprobe.exe in your LocalAppData VideoOptimizerStudio folder. No system PATH edits are required.",
            justify="left",wraplength=900,text_color=("gray38","gray68")
        ).pack(anchor="w",padx=16,pady=(0,15))
        return page
