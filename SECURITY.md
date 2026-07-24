# Security Policy

中文摘要：不要提交真实密钥、Cookie、私密视频、用户隐私、客户数据或未公开资料。腾讯云语音识别凭证只能由使用者在本地环境变量中自行配置，不能写进仓库、示例、issue 或日志。

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

中文报告规则：可以用 GitHub issue 报告可复现的安全问题，但不要在 issue 中包含密钥、私密视频、私密逐字稿或个人数据。
