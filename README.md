# Video Optimizer Studio

A modern Windows video optimizer that combines CPU x265 and NVIDIA NVENC hardware encoding in one application.

## Why two encoder modes?

**CPU • x265**
- Uses `libx265`
- Best compression efficiency / fine quality control
- Useful when you deliberately want to avoid the NVIDIA dGPU
- CPU mode does not initialize/probe NVENC hardware
- Default: CRF 20, medium preset

**GPU • NVIDIA NVENC**
- Uses `hevc_nvenc`
- Much faster and lower CPU load
- Requires a compatible NVIDIA GPU/driver
- Default: CQ 20, P5 HQ preset

**Auto**
- Uses NVENC when available
- Falls back to CPU x265 when it is not

GPU mode never silently falls back to CPU. If the user explicitly chooses GPU and NVENC is unavailable, the app explains the problem instead.

## Preservation behavior

The optimizer intentionally does **not** add FFmpeg `-r` or scaling filters, so the source video resolution and frame timing/FPS are preserved. Output is HEVC (`hvc1`, `yuv420p`) in an MP4 with AAC audio and `+faststart`.

## Features

- Modern dark / light / system CustomTkinter UI
- CPU / GPU / Auto encoder selection
- Multiple-video queue and folder import
- FFprobe metadata preview: resolution, FPS, codec and size
- CPU CRF and x265 preset controls
- GPU CQ and NVENC P1–P7 preset controls
- AAC bitrate selection
- Live per-file and overall progress
- Cancel current batch
- Output-folder and filename-suffix controls
- One-click FFmpeg installer/update inside the app
- Existing system FFmpeg installations are detected automatically
- Custom Windows icon and version metadata
- One-click verified `BUILD_APP.bat`
- GitHub Actions Windows EXE builder
- Regression tests ensuring CPU mode never invokes the GPU and GPU mode never silently falls back

## FFmpeg

If FFmpeg is already in PATH, the app uses it. Otherwise open **FFmpeg → Install / Update FFmpeg**. The app downloads the Windows release essentials build from Gyan.dev and stores `ffmpeg.exe` and `ffprobe.exe` under LocalAppData, without modifying the system PATH.

## Build

Double-click:

```text
BUILD_APP.bat
```

The finished executable will be:

```text
dist\VideoOptimizerStudio.exe
```

## License

MIT
