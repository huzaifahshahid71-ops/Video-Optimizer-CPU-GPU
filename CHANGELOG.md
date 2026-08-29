# Changelog

## v1.0

- Combined the original CPU x265 and GPU NVENC optimizers into one app.
- Added explicit CPU, GPU, and Auto encoder modes.
- CPU mode never uses NVENC; GPU mode never silently falls back to CPU.
- Preserved original source resolution and frame timing/FPS.
- Added a modern CustomTkinter UI with Optimize, Encoder, and FFmpeg pages.
- Added multi-video queue/folder input, metadata preview, live progress, and cancellation.
- Added CPU CRF/preset and GPU CQ/preset controls.
- Added one-click local FFmpeg installation/update.
- Added custom icon, Windows version metadata, regression tests, verified BAT builder, and GitHub Actions.
