import unittest
import inspect
from video_optimizer_engine import EncoderSettings, build_ffmpeg_command, resolve_mode

class EngineTests(unittest.TestCase):
    def test_cpu_forced_never_uses_gpu(self):
        cmd, mode = build_ffmpeg_command("in.mp4","out.mp4",EncoderSettings(mode="CPU"),ffmpeg="ffmpeg",nvenc_available=True)
        self.assertEqual(mode,"CPU")
        self.assertIn("libx265",cmd)
        self.assertNotIn("hevc_nvenc",cmd)
        self.assertNotIn("-r",cmd)
        self.assertNotIn("-vf",cmd)

    def test_gpu_forced_uses_nvenc(self):
        cmd, mode = build_ffmpeg_command("in.mp4","out.mp4",EncoderSettings(mode="GPU"),ffmpeg="ffmpeg",nvenc_available=True)
        self.assertEqual(mode,"GPU")
        self.assertIn("hevc_nvenc",cmd)
        self.assertNotIn("-r",cmd)
        self.assertNotIn("-vf",cmd)

    def test_gpu_forced_fails_without_nvenc(self):
        with self.assertRaises(RuntimeError):
            resolve_mode("GPU",False)

    def test_auto_fallback(self):
        self.assertEqual(resolve_mode("Auto",True),"GPU")
        self.assertEqual(resolve_mode("Auto",False),"CPU")

    def test_cpu_and_gpu_quality_arguments_are_independent(self):
        cpu = EncoderSettings(mode="CPU", cpu_crf=23, gpu_cq=15)
        cmd, mode = build_ffmpeg_command("in.mp4","out.mp4",cpu,ffmpeg="ffmpeg",nvenc_available=True)
        self.assertEqual(mode,"CPU")
        self.assertIn("23",cmd)
        self.assertNotIn("hevc_nvenc",cmd)

        gpu = EncoderSettings(mode="GPU", cpu_crf=30, gpu_cq=17)
        cmd, mode = build_ffmpeg_command("in.mp4","out.mp4",gpu,ffmpeg="ffmpeg",nvenc_available=True)
        self.assertEqual(mode,"GPU")
        self.assertIn("17",cmd)
        self.assertIn("hevc_nvenc",cmd)

if __name__=="__main__":
    unittest.main()
