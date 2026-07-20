#!/usr/bin/env python3
"""Transcribe a local audio file with Tencent Cloud Flash ASR.

Credentials are read from environment variables by the CLI. They are never
accepted as command-line arguments and are never included in returned JSON.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HOST = "asr.cloud.tencent.com"
MAX_AUDIO_BYTES = 100 * 1024 * 1024
SUPPORTED_FORMATS = {"wav", "pcm", "ogg-opus", "speex", "silk", "mp3", "m4a", "aac", "amr"}
ENV_APPID = "TENCENTCLOUD_APPID"
ENV_SECRET_ID = "TENCENTCLOUD_SECRET_ID"
ENV_SECRET_KEY = "TENCENTCLOUD_SECRET_KEY"


class TencentAsrError(RuntimeError):
    pass


def credential_help() -> str:
    return (
        "缺少腾讯云语音识别凭证环境变量。若要启用腾讯云转写，请在你自己的本机环境中设置 "
        "TENCENTCLOUD_APPID、TENCENTCLOUD_SECRET_ID、TENCENTCLOUD_SECRET_KEY。"
        "用途：仅在你明确同意时，把本次临时分析音频提交给腾讯云极速 ASR 生成逐字稿；"
        "不要把这些值写进命令参数、Skill 文件、Git 仓库、日志或对话输出。"
        "未配置时请继续使用本地 faster-whisper，或上传字幕/逐字稿。"
    )


def infer_voice_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix not in SUPPORTED_FORMATS:
        raise TencentAsrError(
            "腾讯极速版不直接支持该文件格式；请先转为 wav、mp3、m4a 或 aac"
        )
    return suffix


def build_request(
    *,
    appid: str,
    secret_id: str,
    secret_key: str,
    audio: bytes,
    voice_format: str,
    timestamp: int | None = None,
    engine_type: str = "16k_zh_en",
) -> Request:
    if not appid or not secret_id or not secret_key:
        raise TencentAsrError(credential_help())
    if voice_format not in SUPPORTED_FORMATS:
        raise TencentAsrError(f"不支持的音频格式：{voice_format}")
    params = {
        "convert_num_mode": 1,
        "engine_type": engine_type,
        "filter_dirty": 0,
        "filter_modal": 0,
        "filter_punc": 0,
        "first_channel_only": 1,
        "secretid": secret_id,
        "speaker_diarization": 0,
        "timestamp": int(time.time()) if timestamp is None else int(timestamp),
        "voice_format": voice_format,
        "word_info": 1,
    }
    query = urlencode(sorted(params.items()))
    path = f"/asr/flash/v1/{appid}"
    sign_source = f"POST{HOST}{path}?{query}".encode("utf-8")
    signature = base64.b64encode(
        hmac.new(secret_key.encode("utf-8"), sign_source, hashlib.sha1).digest()
    ).decode("ascii")
    return Request(
        f"https://{HOST}{path}?{query}",
        data=audio,
        method="POST",
        headers={
            "Authorization": signature,
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(audio)),
        },
    )


def normalize_response(payload: dict[str, Any], *, engine_type: str = "16k_zh_en") -> dict[str, Any]:
    code = int(payload.get("code", -1))
    if code != 0:
        message = str(payload.get("message") or "未知错误")[:300]
        request_id = str(payload.get("request_id") or "unknown")[:100]
        raise TencentAsrError(f"腾讯云识别失败（code={code}, request_id={request_id}）：{message}")

    channel_results = payload.get("flash_result") or []
    transcript = "\n".join(
        str(channel.get("text") or "").strip()
        for channel in channel_results
        if str(channel.get("text") or "").strip()
    )
    segments: list[dict[str, Any]] = []
    for channel in channel_results:
        for sentence in channel.get("sentence_list") or []:
            text = str(sentence.get("text") or "").strip()
            if not text:
                continue
            segment = {
                "start": round(float(sentence.get("start_time", 0)) / 1000, 3),
                "end": round(float(sentence.get("end_time", 0)) / 1000, 3),
                "text": text,
                "speaker_id": sentence.get("speaker_id", 0),
            }
            segments.append(segment)
    return {
        "transcript": transcript,
        "segments": segments,
        "duration_seconds": round(float(payload.get("audio_duration", 0)) / 1000, 3),
        "transcription": {
            "provider": "tencent-cloud-flash-asr",
            "engine": engine_type,
            "request_id": payload.get("request_id"),
        },
    }


def transcribe_file(
    path: Path,
    appid: str,
    secret_id: str,
    secret_key: str,
    *,
    engine_type: str = "16k_zh_en",
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise TencentAsrError("音频文件不存在")
    voice_format = infer_voice_format(path)
    size = path.stat().st_size
    if size <= 0:
        raise TencentAsrError("音频文件为空")
    if size > MAX_AUDIO_BYTES:
        raise TencentAsrError("音频超过腾讯极速版 100 MB 上限")
    audio = path.read_bytes()
    request = build_request(
        appid=appid,
        secret_id=secret_id,
        secret_key=secret_key,
        audio=audio,
        voice_format=voice_format,
        engine_type=engine_type,
    )
    try:
        with opener(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise TencentAsrError(f"腾讯云请求失败（HTTP {exc.code}）") from exc
    except (URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TencentAsrError(f"腾讯云请求失败：{type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise TencentAsrError("腾讯云返回了非对象 JSON")
    return normalize_response(payload, engine_type=engine_type)


def main() -> int:
    parser = argparse.ArgumentParser(description="用腾讯云录音文件识别极速版转写本地音频")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--output", type=Path, help="JSON 输出路径；默认输出到标准输出")
    parser.add_argument("--engine", default="16k_zh_en")
    args = parser.parse_args()
    try:
        result = transcribe_file(
            args.audio,
            os.getenv(ENV_APPID, ""),
            os.getenv(ENV_SECRET_ID, ""),
            os.getenv(ENV_SECRET_KEY, ""),
            engine_type=args.engine,
        )
        status = 0
    except TencentAsrError as exc:
        result = {"transcript": None, "segments": [], "error": str(exc)}
        status = 2
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return status


if __name__ == "__main__":
    sys.exit(main())
