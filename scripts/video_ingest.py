#!/usr/bin/env python3
"""Turn a public Douyin link or local media file into normalized transcript JSON.

Remote media is kept in a temporary directory and removed after transcription.
No browser cookies or account credentials are read by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DOUYIN_HOSTS = {"douyin.com", "www.douyin.com", "v.douyin.com", "iesdouyin.com", "www.iesdouyin.com"}
MAX_DURATION_SECONDS = 30 * 60


class IngestError(RuntimeError):
    pass


def classify_input(value: str) -> tuple[str, str]:
    candidate = value.strip()
    local_path = Path(candidate).expanduser()
    if local_path.is_file():
        return "local-media", str(local_path.resolve())

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise IngestError("输入既不是现有本地文件，也不是 http/https 链接")
    host = (parsed.hostname or "").lower()
    if host in DOUYIN_HOSTS or host.endswith(".douyin.com"):
        return "douyin", candidate
    if host == "weixin.qq.com" and parsed.path.startswith("/sph/"):
        return "wechat-channels", candidate
    raise IngestError(f"当前自动获取仅支持公开抖音链接；未支持域名：{host or 'unknown'}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def base_result(platform: str, source: str) -> dict[str, Any]:
    return {
        "platform": platform,
        "source_url": source if platform != "local-media" else None,
        "local_source": source if platform == "local-media" else None,
        "title": None,
        "author": None,
        "published_at": None,
        "duration_seconds": None,
        "transcript": None,
        "segments": [],
        "summary": None,
        "visual_notes": [],
        "claims": [],
        "uncertainties": [],
        "acquisition_method": "local-media" if platform == "local-media" else "yt-dlp-public-extraction+faster-whisper",
        "acquisition_status": "failed",
        "confidence": "low",
        "copyright_status": "analysis-copy-only",
        "source_content_sha256": None,
        "temporary_media_deleted": platform != "local-media",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def normalize_upload_date(value: Any) -> str | None:
    if not value:
        return None
    text = str(value)
    if re.fullmatch(r"\d{8}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text


def download_public_douyin(url: str, workdir: Path) -> tuple[Path, dict[str, Any]]:
    try:
        import yt_dlp  # type: ignore
    except ImportError as exc:
        raise IngestError(
            "缺少 yt-dlp。请按 references/input-connectors.md 的“本地视频栈安装”完成一次安装"
        ) from exc

    output_template = str(workdir / "source.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "retries": 2,
        "fragment_retries": 2,
        "max_filesize": 300 * 1024 * 1024,
        "restrictfilenames": True,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            metadata = ydl.extract_info(url, download=False)
            duration = metadata.get("duration")
            if duration and float(duration) > MAX_DURATION_SECONDS:
                raise IngestError(f"视频超过 {MAX_DURATION_SECONDS // 60} 分钟安全上限，请改为上传裁剪后的文件")
            metadata = ydl.extract_info(url, download=True)
            requested = metadata.get("requested_downloads") or []
            candidates = [item.get("filepath") for item in requested if item.get("filepath")]
            if metadata.get("_filename"):
                candidates.append(metadata["_filename"])
            for candidate in candidates:
                path = Path(candidate)
                if path.is_file():
                    return path, metadata
            files = [p for p in workdir.iterdir() if p.is_file() and not p.name.endswith((".part", ".ytdl"))]
            if not files:
                raise IngestError("解析器未生成可转写的媒体文件")
            return max(files, key=lambda p: p.stat().st_size), metadata
    except IngestError:
        raise
    except Exception as exc:
        message = str(exc).splitlines()[-1][:500]
        raise IngestError(
            "抖音公开链接获取失败，常见原因是链接失效、地区限制或平台风控。"
            "本脚本不会读取浏览器 Cookie；请上传原视频/录屏继续。"
            f" 原始错误：{message}"
        ) from exc


def transcribe(media_path: Path, model_name: str, language: str | None) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:
        raise IngestError(
            "缺少 faster-whisper。请按 references/input-connectors.md 的“本地视频栈安装”完成一次安装"
        ) from exc

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segment_iter, info = model.transcribe(
        str(media_path),
        language=language,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=True,
    )
    segments: list[dict[str, Any]] = []
    transcript_parts: list[str] = []
    for segment in segment_iter:
        text = segment.text.strip()
        if not text:
            continue
        segments.append({"start": round(segment.start, 2), "end": round(segment.end, 2), "text": text})
        transcript_parts.append(text)
    transcript = "\n".join(transcript_parts).strip()
    details = {
        "detected_language": getattr(info, "language", None),
        "language_probability": round(float(getattr(info, "language_probability", 0.0)), 4),
        "model": model_name,
    }
    return transcript, segments, details


def ingest(value: str, model_name: str, language: str | None) -> dict[str, Any]:
    platform, source = classify_input(value)
    result = base_result(platform, source)
    if platform == "wechat-channels":
        result["uncertainties"].append("微信视频号 sph 链接目前没有满足完整逐字稿要求的稳定无凭证连接器")
        result["acquisition_method"] = "wechat-connector-not-complete"
        return result

    try:
        if platform == "local-media":
            media_path = Path(source)
            metadata: dict[str, Any] = {}
            transcript, segments, details = transcribe(media_path, model_name, language)
        else:
            with tempfile.TemporaryDirectory(prefix="check-information-") as tmp:
                media_path, metadata = download_public_douyin(source, Path(tmp))
                result["source_content_sha256"] = sha256_file(media_path)
                transcript, segments, details = transcribe(media_path, model_name, language)

        result.update({
            "title": metadata.get("title") or metadata.get("description"),
            "author": metadata.get("uploader") or metadata.get("creator"),
            "published_at": normalize_upload_date(metadata.get("upload_date") or metadata.get("timestamp")),
            "duration_seconds": metadata.get("duration"),
            "transcript": transcript or None,
            "segments": segments,
            "acquisition_status": "complete" if transcript else "partial",
            "confidence": "medium" if transcript else "low",
            "transcription": details,
        })
        if platform == "local-media":
            result["source_content_sha256"] = sha256_file(Path(source))
        if not transcript:
            result["uncertainties"].append("本地语音识别没有得到有效文字，请检查音轨或语言设置")
    except IngestError as exc:
        result["uncertainties"].append(str(exc))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="读取公开抖音链接或本地媒体并输出统一内容 JSON")
    parser.add_argument("input", help="抖音分享链接或本地音视频路径")
    parser.add_argument("--output", type=Path, help="JSON 输出路径；默认写到标准输出")
    parser.add_argument("--model", default=os.getenv("CHECK_INFO_WHISPER_MODEL", "small"))
    parser.add_argument("--language", default="zh", help="语音语言；传 auto 自动检测")
    args = parser.parse_args()

    language = None if args.language.lower() == "auto" else args.language
    try:
        result = ingest(args.input, args.model, language)
    except IngestError as exc:
        result = {"acquisition_status": "failed", "uncertainties": [str(exc)]}
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if result.get("acquisition_status") in {"complete", "partial"} else 2


if __name__ == "__main__":
    sys.exit(main())
