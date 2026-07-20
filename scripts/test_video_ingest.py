#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("video_ingest.py")
SPEC = importlib.util.spec_from_file_location("video_ingest", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class VideoIngestTests(unittest.TestCase):
    def test_classifies_douyin_short_link(self):
        self.assertEqual(MODULE.classify_input("https://v.douyin.com/abc123/"), ("douyin", "https://v.douyin.com/abc123/"))

    def test_classifies_douyin_video_link(self):
        self.assertEqual(MODULE.classify_input("https://www.douyin.com/video/1234567890")[0], "douyin")

    def test_classifies_wechat_but_does_not_claim_completion(self):
        result = MODULE.ingest("https://weixin.qq.com/sph/Awncs0yhnO", "small", "zh")
        self.assertEqual(result["platform"], "wechat-channels")
        self.assertEqual(result["acquisition_status"], "failed")
        self.assertIsNone(result["transcript"])

    def test_rejects_unapproved_remote_domain(self):
        with self.assertRaises(MODULE.IngestError):
            MODULE.classify_input("https://example.com/video.mp4")

    def test_normalizes_upload_date(self):
        self.assertEqual(MODULE.normalize_upload_date("20260715"), "2026-07-15")


if __name__ == "__main__":
    unittest.main()
