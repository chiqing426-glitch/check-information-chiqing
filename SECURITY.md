# Security Policy

## Supported Version

This repository is currently an alpha Skill. Security fixes target the `main` branch.

## Sensitive Data Rules

Do not submit:

- Real Tencent Cloud AppID, SecretId, SecretKey, API keys, bearer tokens, cookies, or browser storage.
- User private messages, unpublished contracts, customer data, internal screenshots, or non-public datasets.
- Downloaded videos, temporary media files, transcripts containing personal data, or model caches.

Tencent Cloud ASR credentials must be configured by each user in their own local environment:

```bash
export TENCENTCLOUD_APPID=""
export TENCENTCLOUD_SECRET_ID=""
export TENCENTCLOUD_SECRET_KEY=""
```

These credentials are used only when the user explicitly chooses Tencent Cloud Flash ASR to transcribe temporary analysis audio. The default path remains local transcription or user-provided subtitles.

## Browser Companion Boundary

The Douyin companion is experimental. It must not read cookies, localStorage, account tokens, private messages, recommendation feeds, live streams, or arbitrary network traffic. It should only pass the current Douyin work id and a validated `*.douyinvod.com` `/media-audio-*` URL to the loopback bridge.

## Reporting

Open a GitHub issue for reproducible security problems. Do not include secrets, private videos, private transcripts, or personal data in the issue.
