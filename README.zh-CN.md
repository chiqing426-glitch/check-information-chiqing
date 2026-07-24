# CheckInformation/chiqing

[English](README.md) | [简体中文](README.zh-CN.md)

`CheckInformation/chiqing` 是一个面向短视频创作者和前沿科技使用者的 Codex Skill。它帮助代理读取文案、网页链接、抖音链接、微信视频号链接或本地视频，提取可核验主张，查证时效性产品说法，寻找教程和延展素材，标注素材下载/复用版权状态，并改写成适合中文短视频拍摄的口播稿。

这个项目不是法律意见，不是通用新闻调查工具，也不是绕过平台访问控制的工具。

## 当前状态

当前仓库可作为 `v0.1.0-alpha` 使用。平台视频读取仍属于实验能力，因为抖音、微信视频号和浏览器行为可能随时变化。

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 文案事实核验 | 可用 | 基于用户提供的文字工作。 |
| 公开网页事实核验 | 可用 | 取决于代理当前可用的浏览和读取工具。 |
| 本地音视频转写 | 可用 | 可选安装后使用 `faster-whisper`。 |
| 抖音公开链接读取 | 实验 | 使用 `yt-dlp`，可能受平台风控影响。 |
| 已登录抖音浏览器伴侣 | 实验 | 只捕获 loopback 上的 `*.douyinvod.com` `/media-audio-*` 请求，不读取 Cookie。 |
| 微信视频号 `weixin.qq.com/sph` | 部分可用 | 暂无稳定自动逐字稿连接器；需要用户补充逐字稿、字幕、截图或上传视频。 |
| 腾讯云极速语音识别 | 可选 | 用户必须在本地配置自己的凭证；默认不启用。 |
| 外部素材下载 | 受限 | 只有来源明确允许下载时才下载；复用还需要单独的授权依据。 |

## 安装

把仓库克隆到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
git clone <repo-url> ~/.codex/skills/check-information-chiqing
```

重启或刷新 Codex 后，可以这样调用：

```text
调用 check-information-chiqing，核实这篇内容，找教程与延展素材，并改成口播稿。
```

英文调用示例：

```text
Use check-information-chiqing to fact-check this script/link/video, find tutorials and reference material, label media rights, and rewrite it as a Chinese talking-head script.
```

## 可选视频组件

本地视频转写需要 Python 3.12+ 和 FFmpeg：

```bash
cd ~/.codex/skills/check-information-chiqing
bash scripts/install-video-stack.sh
```

测试一个本地媒体文件：

```bash
.runtime/bin/python scripts/video_ingest.py "/path/to/video.mp4" --output /tmp/check-information-video.json
```

## 可选腾讯云语音识别

腾讯云 ASR 只用于本地 `faster-whisper` 效果不够、且用户明确同意把临时分析音频提交到腾讯云转写的场景。

请在自己的本地 shell 或密钥管理工具里配置：

```bash
export TENCENTCLOUD_APPID=""
export TENCENTCLOUD_SECRET_ID=""
export TENCENTCLOUD_SECRET_KEY=""
```

用途提醒：这些变量只用于提交当前临时分析音频到腾讯云极速语音识别并获取逐字稿。不要把真实值粘贴到聊天、命令参数、Skill 文件、Git 提交、示例、issue 或日志里。

如果没有配置这些变量，Skill 应继续使用本地转写，或要求用户提供字幕/逐字稿。

## 抖音浏览器伴侣

当公开抖音解析失败、但用户已登录浏览器能播放目标页面时，Chrome 伴侣是一个实验性兜底方案。

1. 打开 Chrome 扩展程序页面。
2. 开启开发者模式。
3. 从 `scripts/douyin_companion/` 加载未打包扩展。
4. 启动本地 loopback 桥：

```bash
.runtime/bin/python scripts/douyin_capture_bridge.py --output-dir "$(mktemp -d)" --timeout 120
```

伴侣不请求 Cookie 权限。桥接服务只接受 loopback 请求，验证抖音作品 id，只接受 `*.douyinvod.com` `/media-audio-*` 音轨，并把媒体保存为分析副本。

## 默认交付结构

默认返回五段：

1. 一句话结论。
2. 事实核验表。
3. 教程与延展素材清单。
4. 素材版权与使用说明。
5. 可拍摄中文口播稿。

## 开发

运行本地检查：

```bash
python3 scripts/validate_skill.py .
python3 scripts/secret_scan.py .
python3 -m unittest discover -s scripts -p "test_*.py" -v
node scripts/douyin_companion/test-media-rules.mjs
```

如果要跑完整视频能力，先执行 `bash scripts/install-video-stack.sh`。

贡献规则见 [CONTRIBUTING.md](CONTRIBUTING.md)。欢迎补充双语文档，但默认最终口播稿仍输出简体中文，除非用户另行要求。

## 仓库结构

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

## 许可证

Apache-2.0。见 [LICENSE](LICENSE)。
