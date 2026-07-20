# CheckInformation/chiqing

`CheckInformation/chiqing` is a Codex Skill for Chinese short-form creators and frontier-tech users. It helps an agent read scripts, links, or videos; extract claims; verify time-sensitive product statements; find tutorials and supporting material; label media reuse rights; and rewrite the result into a shoot-ready Chinese talking-head script.

This project is not legal advice, a universal news investigation tool, or a bypass for platform access controls.

## Status

This repository is ready for `v0.1.0-alpha` use. Treat platform video ingestion as experimental because Douyin, WeChat Channels, and browser behavior can change without notice.

| Capability | Status | Notes |
| --- | --- | --- |
| Script fact-checking | Usable | Works from user-provided text. |
| Public webpage fact-checking | Usable | Depends on the agent's available browsing tools. |
| Local audio/video transcription | Usable | Uses `faster-whisper` after optional setup. |
| Public Douyin link ingestion | Experimental | Uses `yt-dlp`; may fail under platform risk controls. |
| Logged-in Douyin browser companion | Experimental | Captures only `*.douyinvod.com` `/media-audio-*` requests over loopback; no cookies. |
| WeChat Channels `weixin.qq.com/sph` | Partial | No stable automatic transcript connector yet. Ask the user for transcript, subtitle, screenshots, or upload. |
| Tencent Cloud Flash ASR | Optional | User must configure their own credentials locally. Disabled unless explicitly used. |
| External media download | Restricted | Download only when source explicitly permits it; reuse requires a separate license basis. |

## Install

Clone the repository into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
git clone <repo-url> ~/.codex/skills/check-information-chiqing
```

Restart or refresh Codex, then call:

```text
调用 check-information-chiqing，核实这篇内容，找教程与延展素材，并改成口播稿。
```

## Optional Video Stack

Local video transcription requires Python 3.12+ and FFmpeg:

```bash
cd ~/.codex/skills/check-information-chiqing
bash scripts/install-video-stack.sh
```

Then test a local media file:

```bash
.runtime/bin/python scripts/video_ingest.py "/path/to/video.mp4" --output /tmp/check-information-video.json
```

## Optional Tencent Cloud ASR

Tencent Cloud ASR is only for cases where local `faster-whisper` is not good enough and the user explicitly agrees to submit the temporary analysis audio to Tencent Cloud.

Configure these variables in your own local shell or secret manager:

```bash
export TENCENTCLOUD_APPID=""
export TENCENTCLOUD_SECRET_ID=""
export TENCENTCLOUD_SECRET_KEY=""
```

Purpose reminder for users: these values are used only to submit the current temporary analysis audio to Tencent Cloud Flash ASR and receive a transcript. Do not paste real values into a chat, command arguments, Skill files, Git commits, examples, issue reports, or logs.

If these variables are missing, the Skill should keep using local transcription or ask the user for subtitles/transcript.

## Douyin Companion

The Chrome companion is an experimental fallback when a public Douyin page plays in the user's logged-in browser but public extraction fails.

1. Open Chrome extensions.
2. Enable developer mode.
3. Load unpacked extension from `scripts/douyin_companion/`.
4. Start the loopback bridge:

```bash
.runtime/bin/python scripts/douyin_capture_bridge.py --output-dir "$(mktemp -d)" --timeout 120
```

The companion does not request cookie permission. The bridge accepts only loopback requests, validates the Douyin work id, accepts only `*.douyinvod.com` `/media-audio-*` tracks, and stores the media as an analysis copy only.

## Output Contract

By default the Skill returns five sections:

1. One-line conclusion.
2. Fact-check table.
3. Tutorial and extended material list.
4. Media rights and usage notes.
5. Shoot-ready Chinese talking-head script.

## Development

Run local checks:

```bash
python3 scripts/validate_skill.py .
python3 scripts/secret_scan.py .
python3 -m unittest discover -s scripts -p "test_*.py" -v
node scripts/douyin_companion/test-media-rules.mjs
```

For full video tests, run `bash scripts/install-video-stack.sh` first.

## Repository Layout

```text
check-information-chiqing/
├── SKILL.md
├── agents/openai.yaml
├── references/
├── scripts/
├── examples/
├── evals/
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

## License

Apache-2.0. See [LICENSE](LICENSE).
