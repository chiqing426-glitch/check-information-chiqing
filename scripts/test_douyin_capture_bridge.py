#!/usr/bin/env python3
import importlib.util
import io
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("douyin_capture_bridge.py")
SPEC = importlib.util.spec_from_file_location("douyin_capture_bridge", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CaptureBridgeTests(unittest.TestCase):
    def valid_payload(self):
        return {
            "aweme_id": "7662394418871209251",
            "source_url": "https://www.douyin.com/video/7662394418871209251",
            "media_url": "https://v26-web.douyinvod.com/path/media-audio-und-mp4a/?token=ephemeral",
        }

    def test_accepts_matching_douyin_capture(self):
        capture = MODULE.validate_capture(self.valid_payload())
        self.assertEqual(capture.aweme_id, "7662394418871209251")

    def test_rejects_mismatched_aweme_id(self):
        payload = self.valid_payload()
        payload["aweme_id"] = "1"
        with self.assertRaises(MODULE.CaptureError):
            MODULE.validate_capture(payload)

    def test_rejects_non_douyin_cdn(self):
        payload = self.valid_payload()
        payload["media_url"] = "https://attacker.example/path/media-audio-und-mp4a/"
        with self.assertRaises(MODULE.CaptureError):
            MODULE.validate_capture(payload)

    def test_rejects_video_only_track(self):
        payload = self.valid_payload()
        payload["media_url"] = "https://v26-web.douyinvod.com/path/media-video-avc1/?token=ephemeral"
        with self.assertRaises(MODULE.CaptureError):
            MODULE.validate_capture(payload)

    def test_rejects_lookalike_domain(self):
        payload = self.valid_payload()
        payload["media_url"] = "https://douyinvod.com.attacker.example/path/media-audio-und-mp4a/"
        with self.assertRaises(MODULE.CaptureError):
            MODULE.validate_capture(payload)

    def test_copy_limited_enforces_size(self):
        with self.assertRaises(MODULE.CaptureError):
            MODULE.copy_limited(io.BytesIO(b"12345"), io.BytesIO(), limit=4)


if __name__ == "__main__":
    unittest.main()
