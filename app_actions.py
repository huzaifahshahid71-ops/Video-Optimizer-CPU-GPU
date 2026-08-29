from __future__ import annotations
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

from video_optimizer_engine import (
    EncoderSettings, EncodingCancelled, VideoInfo, VIDEO_EXTENSIONS,
    find_ffmpeg_pair, has_nvenc, install_ffmpeg, output_path_for,
    probe_video, encode_video,
)

class ActionsMixin:
    def add_videos(self):
        paths=filedialog.askopenfilenames(title="Add videos",filetypes=[("Video files","*.mp4 *.mov *.mkv *.webm *.avi *.m4v"),("All files","*.*")])
        if paths: self._append_paths([Path(p) for p in paths])

    def add_folder(self):
        folder=filedialog.askdirectory(title="Add all videos from folder")
        if not folder: return
        paths=[p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]
        self._append_paths(paths)

    def _append_paths(self, paths):
        unique=[p for p in paths if p not in self.video_paths]
        if not unique: return
        self.video_paths.extend(unique)
        self.queue_text.set(f"{len(self.video_paths)} video{'s' if len(self.video_paths)!=1 else ''}")
        self.status_text.set(f"Analyzing {len(unique)} video(s)…")
        threading.Thread(target=self._probe_paths,args=(unique,),daemon=True).start()

    def _probe_paths(self, paths):
        for p in paths:
            try:
                info=probe_video(p)
                self.video_infos[p]=info
            except Exception:
                info=VideoInfo(path=p,size_bytes=p.stat().st_size if p.exists() else 0)
                self.video_infos[p]=info
            self.after(0,self._refresh_tree)
        self.after(0,lambda:self.status_text.set("Queue ready."))

    def _refresh_tree(self):
        selected={self.tree.set(i,"name") for i in self.tree.selection()}
        for i in self.tree.get_children(): self.tree.delete(i)
        for p in self.video_paths:
            info=self.video_infos.get(p,VideoInfo(path=p))
            item=self.tree.insert("", "end", values=(p.name,info.resolution,info.fps_text,info.codec,info.size_text))
            if p.name in selected: self.tree.selection_add(item)

    def remove_selected(self):
        names={self.tree.set(i,"name") for i in self.tree.selection()}
        if not names: return
        self.video_paths=[p for p in self.video_paths if p.name not in names]
        for p in list(self.video_infos):
            if p.name in names: self.video_infos.pop(p,None)
        self._refresh_tree()
        self.queue_text.set(f"{len(self.video_paths)} video{'s' if len(self.video_paths)!=1 else ''}")

    def clear_videos(self):
        if self.encoding: return
        self.video_paths.clear()
        self.video_infos.clear()
        self._refresh_tree()
        self.queue_text.set("0 videos")
        self.progress.set(0)
        self.progress_text.set("0%")
        self.status_text.set("Add a video to begin.")

    def pick_output_folder(self):
        p=filedialog.askdirectory(title="Output folder")
        if p: self.output_folder.set(p)

    def refresh_environment(self):
        ffmpeg,ffprobe=find_ffmpeg_pair()
        nv=has_nvenc(ffmpeg) if ffmpeg else False
        if ffmpeg and ffprobe:
            self.encoder_status.set("NVENC ready" if nv else "CPU ready")
            self.ffmpeg_detail.configure(
                text=f"FFmpeg: {ffmpeg}\nFFprobe: {ffprobe}\nNVIDIA HEVC NVENC: {'Available' if nv else 'Not available'}"
            )
        else:
            self.encoder_status.set("FFmpeg missing")
            self.ffmpeg_detail.configure(text="FFmpeg/FFprobe were not found. Use Install / Update FFmpeg below.")
        return ffmpeg,ffprobe,nv

    def install_ffmpeg_clicked(self):
        if self.encoding: return
        self.install_btn.configure(state="disabled")
        self.install_progress.set(0)
        self.install_text.set("Starting download…")
        threading.Thread(target=self._install_ffmpeg_worker,daemon=True).start()

    def _install_ffmpeg_worker(self):
        try:
            install_ffmpeg(lambda p,t:self.after(0,lambda p=p,t=t:(self.install_progress.set(p),self.install_text.set(t))))
            self.after(0,self.refresh_environment)
            self.after(0,lambda:messagebox.showinfo("FFmpeg ready","FFmpeg and FFprobe were installed successfully."))
        except Exception as exc:
            self.after(0,lambda e=str(exc):messagebox.showerror("FFmpeg installation failed",e))
        finally:
            self.after(0,lambda:self.install_btn.configure(state="normal"))

    def _settings(self):
        return EncoderSettings(
            mode=self.encoder_mode.get(),
            cpu_preset=self.cpu_preset.get(),
            cpu_crf=int(self.cpu_crf.get()),
            gpu_preset=self.gpu_preset.get(),
            gpu_cq=int(self.gpu_cq.get()),
            audio_bitrate=self.audio_bitrate.get(),
            overwrite=bool(self.overwrite.get()),
            suffix=self.output_suffix.get() or "_optimized",
        )

    def start_encoding(self):
        if self.encoding: return
        if not self.video_paths:
            messagebox.showwarning("No videos","Add at least one video first.")
            return
        ffmpeg,ffprobe=find_ffmpeg_pair()
        if not ffmpeg or not ffprobe:
            if messagebox.askyesno("FFmpeg required","FFmpeg is not installed. Open the FFmpeg page now?"):
                self.show_page("FFmpeg")
            return
        nv=has_nvenc(ffmpeg)
        if self.encoder_mode.get()=="GPU" and not nv:
            messagebox.showerror("GPU encoder unavailable","GPU mode requires NVIDIA HEVC NVENC, but it is not available on this system.\n\nChoose CPU or Auto, or update your NVIDIA driver/FFmpeg build.")
            return
        self.encoding=True
        self.cancel_event.clear()
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress.set(0)
        self.progress_text.set("0%")
        settings=self._settings()
        paths=list(self.video_paths)
        output_dir=self.output_folder.get()
        self.worker=threading.Thread(target=self._encode_queue,args=(paths,settings,ffmpeg,nv,output_dir),daemon=True)
        self.worker.start()

    def _encode_queue(self,paths,settings,ffmpeg,nv,output_dir):
        try:
            total=len(paths)
            for idx,p in enumerate(paths):
                if self.cancel_event.is_set(): raise EncodingCancelled("Encoding cancelled.")
                info=self.video_infos.get(p)
                if not info or not info.duration:
                    info=probe_video(p)
                    self.video_infos[p]=info
                out=output_path_for(p,output_dir,settings.suffix)
                self.after(0,lambda i=idx+1,t=total,n=p.name:self.status_text.set(f"Encoding {i}/{t}: {n}"))
                actual=encode_video(
                    p,out,info,settings,ffmpeg=ffmpeg,nvenc_available=nv,
                    progress_cb=lambda pct,speed,mode,i=idx,t=total:self._progress_from_worker(i,t,pct,speed,mode),
                    cancel_event=self.cancel_event
                )
                try:
                    out_info=probe_video(out)
                    preserved=(out_info.width==info.width and out_info.height==info.height and abs(out_info.fps-info.fps)<0.05)
                    self.after(0,lambda ok=preserved,o=out:self.detail_text.set(
                        f"Saved {o.name} • resolution/FPS {'verified' if ok else 'check recommended'}"
                    ))
                except Exception:
                    pass
            self.after(0,lambda:messagebox.showinfo("Done","All videos were optimized successfully."))
            self.after(0,lambda:self.status_text.set("Optimization complete."))
            self.after(0,lambda:self.progress_text.set("100%"))
            self.after(0,lambda:self.progress.set(1))
        except EncodingCancelled:
            self.after(0,lambda:self.status_text.set("Cancelled."))
            self.after(0,lambda:self.detail_text.set("The current encoding was stopped."))
        except Exception as exc:
            self.after(0,lambda e=str(exc):messagebox.showerror("Optimization failed",e))
            self.after(0,lambda:self.status_text.set("Optimization failed."))
        finally:
            self.after(0,self._encoding_finished)

    def _progress_from_worker(self,index,total,pct,speed,mode):
        overall=(index+pct)/max(1,total)
        def apply():
            self.progress.set(overall)
            self.progress_text.set(f"{overall*100:.1f}%")
            self.detail_text.set(f"{mode} encoder • current file {pct*100:.1f}% • speed {speed}")
        self.after(0,apply)

    def _encoding_finished(self):
        self.encoding=False
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

    def cancel_encoding(self):
        if self.encoding:
            self.cancel_event.set()
            self.status_text.set("Cancelling…")

    def _close_app(self):
        if self.encoding:
            if not messagebox.askyesno("Encoding in progress","Stop encoding and exit?"):
                return
            self.cancel_event.set()
        self.destroy()
