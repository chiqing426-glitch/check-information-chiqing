#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("tencent_flash_asr.py")
SPEC = importlib.util.spec_from_file_location("tencent_flash_asr", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


class TencentFlashAsrTests(unittest.TestCase):
    def test_build_request_uses_sorted_query_and_hmac_signature(self):
        request = MODULE.build_request(
            appid="123456",
            secret_id="test-id",
            secret_key="test-key",
            audio=b"audio",
            voice_format="aac",
            timestamp=1700000000,
        )
        self.assertEqual(request.full_url, (
            "https://asr.cloud.tencent.com/asr/flash/v1/123456?"
            "convert_num_mode=1&engine_type=16k_zh_en&filter_dirty=0&filter_modal=0&"
            "filter_punc=0&first_channel_only=1&secretid=test-id&speaker_diarization=0&"
            "timestamp=1700000000&voice_format=aac&word_info=1"
        ))
        self.assertEqual(request.headers["Authorization"], "kTTTqfDbeZt/1Mo3ISKrgkZoL54=")
        self.assertNotIn("test-key", request.full_url)
        self.assertEqual(request.data, b"audio")

    def test_normalizes_transcript_and_timestamped_segments(self):
        result = MODULE.normalize_response({
            "code": 0,
            "message": "",
            "request_id": "req-1",
            "audio_duration": 2450,
            "flash_result": [{
                "text": "一旦察觉状态不对，就要把自己救上来。",
                "sentence_list": [
                    {"text": "一旦察觉状态不对，", "start_time": 0, "end_time": 1200, "speaker_id": 0},
                    {"text": "就要把自己救上来。", "start_time": 1200, "end_time": 2450, "speaker_id": 0},
                ],
            }],
        }, engine_type="16k_zh")
        self.assertEqual(result["transcript"], "一旦察觉状态不对，就要把自己救上来。")
        self.assertEqual(result["segments"][1], {
            "start": 1.2, "end": 2.45, "text": "就要把自己救上来。", "speaker_id": 0
        })
        self.assertEqual(result["duration_seconds"], 2.45)
        self.assertEqual(result["transcription"]["engine"], "16k_zh")

    def test_api_error_is_safe_and_does_not_expose_credentials(self):
        with self.assertRaisesRegex(MODULE.TencentAsrError, "4003") as raised:
            MODULE.normalize_response({"code": 4003, "message": "服务未开通", "request_id": "req-2"})
        self.assertNotIn("Secret", str(raised.exception))

    def test_missing_credentials_explains_user_configuration(self):
        with self.assertRaisesRegex(MODULE.TencentAsrError, "TENCENTCLOUD_APPID") as raised:
            MODULE.build_request(
                appid="",
                secret_id="",
                secret_key="",
                audio=b"audio",
                voice_format="aac",
                timestamp=1700000000,
            )
        message = str(raised.exception)
        self.assertIn("你自己的本机环境", message)
        self.assertIn("临时分析音频", message)
        self.assertNotIn("AKID", message)

    def test_rejects_unsupported_file_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clip.txt"
            path.write_text("not audio", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.TencentAsrError, "格式"):
                MODULE.transcribe_file(path, "1", "id", "key")

    def test_transcribe_file_does_not_return_credentials(self):
        captured = {}

        def fake_open(request, timeout):
            captured["request"] = request
            return FakeResponse({
                "code": 0,
                "message": "",
                "request_id": "req-3",
                "audio_duration": 1000,
                "flash_result": [{"text": "测试成功。", "sentence_list": []}],
            })

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clip.aac"
            path.write_bytes(b"audio")
            result = MODULE.transcribe_file(path, "1", "secret-id", "secret-key", opener=fake_open)
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("secret-id", serialized)
        self.assertNotIn("secret-key", serialized)
        self.assertEqual(result["transcript"], "测试成功。")


if __name__ == "__main__":
    unittest.main()
