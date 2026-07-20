#!/usr/bin/env python3
"""Receive an ephemeral Douyin media URL from the local Chrome companion.

The bridge listens on loopback only, accepts no cookies or authorization
headers, validates every URL, and writes one temporary analysis copy.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 17321
MAX_REQUEST_BYTES = 64 * 1024
MAX_MEDIA_BYTES = 100 * 1024 * 1024
AWEME_ID = re.compile(r"^/video/(\d+)(?:/)?$")
MEDIA_PATH = re.compile(r"/media-audio-", re.IGNORECASE)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
)


class CaptureError(RuntimeError):
    pass


@dataclass(frozen=True)
class CaptureRequest:
    aweme_id: str
    source_url: str
    media_url: str


def is_allowed_media_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    return host == "douyinvod.com" or host.endswith(".douyinvod.com")


def validate_capture(payload: dict[str, Any]) -> CaptureRequest:
    aweme_id = str(payload.get("aweme_id") or "")
    source_url = str(payload.get("source_url") or "")
    media_url = str(payload.get("media_url") or "")
    if not aweme_id.isdigit():
        raise CaptureError("作品 ID 无效")

    source = urlparse(source_url)
    match = AWEME_ID.fullmatch(source.path)
    if source.scheme != "https" or source.hostname != "www.douyin.com" or not match:
        raise CaptureError("来源页不是受支持的抖音作品页")
    if match.group(1) != aweme_id:
        raise CaptureError("作品 ID 与来源页不一致")

    media = urlparse(media_url)
    if media.scheme != "https" or not is_allowed_media_host(media.hostname or ""):
        raise CaptureError("媒体地址不属于允许的抖音 CDN")
    if not MEDIA_PATH.search(media.path):
        raise CaptureError("媒体地址缺少可识别的音频轨道")
    if media.username or media.password or media.fragment:
        raise CaptureError("媒体地址包含不允许的凭证或片段")
    return CaptureRequest(aweme_id=aweme_id, source_url=source_url, media_url=media_url)


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or not is_allowed_media_host(parsed.hostname or ""):
            raise CaptureError("媒体下载重定向到了未授权域名")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def copy_limited(source: BinaryIO, destination: BinaryIO, limit: int = MAX_MEDIA_BYTES) -> int:
    total = 0
    while True:
        chunk = source.read(1024 * 1024)
        if not chunk:
            return total
        total += len(chunk)
        if total > limit:
            raise CaptureError(f"媒体超过 {limit // (1024 * 1024)} MB 安全上限")
        destination.write(chunk)


def download_media(capture: CaptureRequest, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    partial = output_dir / f"douyin-{capture.aweme_id}-audio.mp4.part"
    final = output_dir / f"douyin-{capture.aweme_id}-audio.mp4"
    request = Request(
        capture.media_url,
        headers={"Referer": "https://www.douyin.com/", "User-Agent": USER_AGENT},
    )
    opener = build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=30) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            if not (content_type.startswith("audio/") or content_type.startswith("video/")):
                raise CaptureError(f"媒体响应类型异常：{content_type or 'unknown'}")
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_MEDIA_BYTES:
                raise CaptureError("媒体超过安全上限")
            with partial.open("wb") as handle:
                size = copy_limited(response, handle)
            if size == 0:
                raise CaptureError("媒体响应为空")
        partial.replace(final)
        return final
    except (HTTPError, URLError, OSError, ValueError) as exc:
        raise CaptureError(f"媒体下载失败：{type(exc).__name__}") from exc
    finally:
        partial.unlink(missing_ok=True)


class CaptureServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler, output_dir: Path):
        super().__init__(address, handler)
        self.output_dir = output_dir
        self.capture_path: Path | None = None
        self.capture_error: str | None = None
        self.done = threading.Event()


class CaptureHandler(BaseHTTPRequestHandler):
    server: CaptureServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _origin(self) -> str | None:
        origin = self.headers.get("Origin")
        return origin if origin and origin.startswith("chrome-extension://") else None

    def _headers(self, status: int, content_type: str = "application/json") -> None:
        self.send_response(status)
        origin = self._origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        self._headers(status)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self) -> None:
        if self.path != "/capture" or not self._origin():
            self._json(403, {"ok": False, "error": "origin-not-allowed"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self._origin() or "")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"ok": True, "service": "check-information-douyin-bridge"})
        else:
            self._json(404, {"ok": False})

    def do_POST(self) -> None:
        if self.path != "/capture":
            self._json(404, {"ok": False})
            return
        if not self._origin():
            self._json(403, {"ok": False, "error": "origin-not-allowed"})
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise CaptureError("请求大小无效")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise CaptureError("请求必须是 JSON 对象")
            capture = validate_capture(payload)
            path = download_media(capture, self.server.output_dir)
            self.server.capture_path = path
            self._json(200, {"ok": True, "aweme_id": capture.aweme_id})
        except (CaptureError, json.JSONDecodeError) as exc:
            self.server.capture_error = str(exc)
            self._json(400, {"ok": False, "error": str(exc)})
        finally:
            if self.server.capture_path:
                self.server.done.set()


def serve_once(output_dir: Path, host: str, port: int, timeout: int) -> Path:
    if host not in {"127.0.0.1", "localhost"}:
        raise CaptureError("安全限制：服务只能监听本机回环地址")
    server = CaptureServer((host, port), CaptureHandler, output_dir)
    server.timeout = 1
    deadline = time.monotonic() + timeout
    try:
        print(json.dumps({"status": "waiting", "url": f"http://{host}:{port}/health"}, ensure_ascii=False), flush=True)
        while time.monotonic() < deadline and not server.done.is_set():
            server.handle_request()
        if not server.capture_path:
            detail = f"；最后错误：{server.capture_error}" if server.capture_error else ""
            raise CaptureError(f"等待抖音媒体超时{detail}")
        return server.capture_path
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="等待本机 Chrome 伴侣提交一条抖音媒体轨道")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    try:
        path = serve_once(args.output_dir.expanduser().resolve(), args.host, args.port, args.timeout)
    except (CaptureError, OSError, socket.error) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": "complete", "path": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
