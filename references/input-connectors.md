# 输入连接器

## 路由顺序

1. 识别纯文案、普通网页、平台视频链接和本地音视频文件。
2. 普通网页优先读取正文和页面内公开字幕。
3. 平台视频优先读取官方字幕或公开文字稿；没有字幕时再获取音频并转写。
4. 匹配 `v.douyin.com` 或 `douyin.com/video/` 时，执行抖音连接器。
5. 匹配 `https://weixin.qq.com/sph/` 时，执行微信视频号连接器。
6. 所有连接器失败后，要求用户提供视频、录屏、字幕或关键截图。

## 抖音连接器（最低可用入口）

目标是让用户直接粘贴公开抖音分享链接，取得可用于后续核验的逐字稿。先使用 `yt-dlp` 获取公开媒体；抖音要求新鲜会话时，回退到用户已登录的浏览器会话和本机读取伴侣；取得媒体后用 `faster-whisper` 在本地转写。这些组件是实现依赖，不是事实证据来源。

### 本地视频栈安装

首次使用时，在 Skill 目录创建独立环境，避免污染系统 Python：

```bash
python3 -m venv .runtime
.runtime/bin/python -m pip install --no-cache-dir -r scripts/requirements-video.txt
```

需要系统可用的 FFmpeg。不要把 `.runtime`、模型缓存或临时视频提交到开源仓库。

### 执行

```bash
.runtime/bin/python scripts/video_ingest.py "<抖音分享链接>" --output /tmp/check-information-video.json
```

执行规则：

1. 只自动接收公开的 `v.douyin.com`、`douyin.com/video/` 及同属抖音的链接；其他域名不得送进下载器。
2. 不读取、复制或导出浏览器 Cookie，不要求用户提交账号密码。公开解析被风控拦截时，进入浏览器会话模式。
3. 远程媒体只保存在系统临时目录，完成转写后自动删除；持久化输出只包含元数据、逐字稿、时间戳和内容哈希。
4. 默认限制 30 分钟和 300 MB，避免误处理直播、合集或超大文件。
5. `complete` 只代表已经取得可读逐字稿，不代表逐字稿、标题或作者完全准确。事实主张仍需独立核验。
6. 自动语音识别可能误写人名、产品名、数字和中英文混合术语。把这些词列入 `uncertainties`，结合画面字幕或官方来源复核。
7. 连接器暂不声称自动理解全部画面。若主张依赖界面操作、前后对比或画面文字，必须再读取关键帧、截图或用户提供的画面材料。

### 腾讯云中文转写（可选后端）

当本地 `faster-whisper` 的中文效果不足，且用户明确同意把临时音频提交给腾讯云时，可改用录音文件识别极速版。默认仍是本地转写；云端后端不得静默启用。

向用户提示配置时，使用这个口径：`如果你想启用腾讯云转写，请在你自己的本机环境中设置 TENCENTCLOUD_APPID、TENCENTCLOUD_SECRET_ID、TENCENTCLOUD_SECRET_KEY。它们只用于把本次临时分析音频提交给腾讯云极速 ASR 生成逐字稿；不要把真实值发到对话、命令参数、Skill 文件、Git 仓库或日志里。未配置时我会继续使用本地转写，或请你上传字幕/逐字稿。`

安全与数据规则：

1. 只从 `TENCENTCLOUD_APPID`、`TENCENTCLOUD_SECRET_ID`、`TENCENTCLOUD_SECRET_KEY` 环境变量读取凭证；禁止把密钥放进命令参数、Skill、仓库、配置示例、输出 JSON 或日志。
2. 用户在聊天或日志中粘贴过长期密钥时，完成测试后提醒其在腾讯云控制台轮换密钥。
3. 上传前说明数据流向；仅上传为本次内容核验取得的临时分析音轨，转写结束后删除音频。
4. 极速版直接支持 `wav`、`mp3`、`m4a`、`aac` 等格式，单文件上限 100 MB、2 小时。扩展抓到 MP4 容器中的 AAC 音轨时，先用 FFmpeg 无损封装为 M4A。
5. 中文普通话优先尝试 `16k_zh`；只有账号开通相应大模型计费且确有中英混合、方言或低质量音频需求时，才使用 `16k_zh_en`。
6. `4004` 表示资源包耗尽或账号未开通可用计费，不得循环重试或擅自开通付费；改用已有额度的引擎，仍失败则回退本地转写。

执行示例（环境变量应在用户自己的安全环境中设置，不要写进脚本）：

```bash
ffmpeg -i temporary-audio.mp4 -vn -c:a copy temporary-audio.m4a
.runtime/bin/python scripts/tencent_flash_asr.py temporary-audio.m4a --engine 16k_zh --output /tmp/tencent-asr.json
```

转写 JSON 只含逐字稿、时间段、时长、引擎名称和请求 ID。人名、书名、产品名、数字与同音词仍需结合字幕或原画面复核。

### 已登录浏览器会话模式

当公开解析出现 `Fresh cookies`、登录限制或目标页正文为空时：

1. 使用支持现有登录状态的浏览器打开原始分享链接；未登录时请用户自行登录，完成后继续，不代填手机号、验证码或密码。
2. 确认页面展示的作品 ID、作者或标题与目标链接一致；若只出现推荐视频，获取状态仍为 `failed`。
3. 优先读取平台公开字幕或页面中目标作品的可见文字。抖音的“章节要点”或 AI 摘要只能生成 `partial` 结果，不能冒充逐字稿。
4. 没有字幕时，只对目标作品的 `<video>`、音频或浏览器明确暴露的页面媒体执行下载。必须核对目标作品时长、ID或标题，避免误取推荐视频。
5. 不从浏览器读取 Cookie、localStorage、账号令牌或隐蔽接口响应；不把登录状态复制到命令行下载器。
6. 页面媒体仅作为 `analysis-copy-only` 临时分析副本。保存到临时路径后运行：

```bash
.runtime/bin/python scripts/video_ingest.py "/temporary/path/to/media" --output /tmp/check-information-video.json
```

7. 转写完成后删除临时媒体。逐字稿进入后续核验；源视频仍不得作为可复用素材交付。

### Chrome 本机读取伴侣（实验性）

当页面能正常播放、但浏览器只暴露 `blob:` 视频地址时，可使用 `scripts/douyin_companion/` 中的 Manifest V3 扩展配合本机桥接器。它监听当前作品实际发出的 `douyinvod.com` 音视频轨道请求，只把临时媒体 URL 和作品 ID 发送到 `127.0.0.1:17321`；扩展不申请 `cookies` 权限，桥接器也不接收 Cookie、Authorization 或账号令牌。

首次使用必须由用户在 Chrome 扩展管理页手动选择“加载已解压的扩展程序”，目录为：

```text
scripts/douyin_companion/
```

每次读取按以下顺序执行：

```bash
tmpdir="$(mktemp -d)"
.runtime/bin/python scripts/douyin_capture_bridge.py --output-dir "$tmpdir" --timeout 120
```

1. 先启动本机桥接器，再在已登录 Chrome 中打开目标 `https://www.douyin.com/video/<作品ID>` 页面并播放目标作品。
2. 桥接器只监听本机回环地址；只接受来源为 Chrome 扩展的请求、匹配当前作品 ID 的抖音页面，以及 `*.douyinvod.com` 的 `media-audio-*` 音频轨道。不得把无声画面轨道标记为获取成功。
3. 下载请求只补充正常的抖音 `Referer` 和浏览器 `User-Agent`，不附带 Cookie。所有重定向必须仍位于允许的抖音 CDN。
4. 桥接器成功后输出临时媒体路径；立即运行 `video_ingest.py` 转写该本地文件，然后删除整个临时目录。
5. 这是读取用户当前可播放内容的本地辅助工具，不是绕过权限、付费、地区限制或已删除内容的下载器。媒体副本只能标为 `analysis-copy-only`。
6. 扩展目前只匹配独立作品页，不读取推荐流、直播、私信或账号存储。若页面不播放或 CDN 域名发生变化，状态仍为 `failed`，不得放宽到任意网络域名。

### 失败回退

若结果为 `failed`：

1. 确认链接仍公开有效，并仅重试一次。
2. 尝试一次已登录浏览器会话；目标作品仍不可见或无法取得媒体时停止。
3. 不循环更换第三方解析站，不尝试窃取或复用登录 Cookie。
4. 请用户直接上传原视频、合法保存的副本或录屏，再用同一脚本处理本地文件。
5. 只有标题或网页摘要时停止，不进入事实核验和口播改写。

本地文件执行示例：

```bash
.runtime/bin/python scripts/video_ingest.py "/path/to/video.mp4" --output /tmp/check-information-video.json
```

## 微信视频号连接器

按以下顺序获取内容：

1. 若运行环境配置了用户明确授权的专用视频号解析接口，提交公开分享链接并取得字幕、逐字稿或媒体；记录服务名称和数据流向，不读取账号 Cookie。
2. 没有专用接口时，可使用腾讯元宝网页补充元数据，但不得预期它能返回逐字稿。
3. 仍未取得视频正文时，要求用户在微信中把视频卡片转发给元宝并复制逐字稿，或上传原视频、录屏、字幕和关键截图。

只有取得 `transcript`、平台字幕或可验证的媒体内容时，才把获取状态标为 `complete`。

### 腾讯元宝网页元数据模式

将腾讯元宝视为外部内容获取服务，不把其回答直接视为事实来源。

1. 使用支持现有登录状态的浏览器打开 `https://yuanbao.tencent.com/`。
2. 未登录时停下，请用户自行扫码或登录；不要读取、复制、导出或保存 Cookie、令牌和账号凭证。
3. 发送前说明会把用户提供的视频号链接和提取指令提交给腾讯元宝，并按浏览器交互规则确认。
4. 新建独立对话，提交以下指令，把链接替换为用户输入：

```text
请读取这个微信视频号链接，并只依据视频本身输出内容，不要搜索或补充外部事实：
<URL>

请严格输出以下 JSON；无法获取的字段使用 null，不要猜测：
{
  "title": null,
  "author": null,
  "published_at": null,
  "duration_seconds": null,
  "transcript": null,
  "summary": null,
  "visual_notes": [],
  "claims": [],
  "uncertainties": []
}

transcript 必须尽量保留原口播顺序；如果只能总结而不能逐字转写，请将 transcript 设为 null，并在 uncertainties 中说明。
```

5. 等待生成完成，读取回答并提取 JSON。若回答包含说明性文字，只提取明确的 JSON 对象；无法可靠解析时重试一次，要求“仅返回合法 JSON”。
6. 验证 `transcript` 是否非空。只有摘要而没有逐字稿、字幕或画面信息时，只能作为元数据结果，获取状态标为 `partial`，不得据此完整核验视频。
7. 不把元宝生成的标题、作者、日期、摘要和逐字稿自动当作准确。与页面可见信息、用户截图或其他来源冲突时，以原始页面信息为准并标记冲突。

## 统一视频内容数据

把连接器结果转换为：

```json
{
  "platform": "douyin-or-wechat-channels",
  "source_url": "",
  "title": null,
  "author": null,
  "published_at": null,
  "duration_seconds": null,
  "transcript": null,
  "summary": null,
  "visual_notes": [],
  "claims": [],
  "uncertainties": [],
  "acquisition_method": "yt-dlp-public-extraction+faster-whisper-or-wechat-fallback",
  "acquisition_status": "partial",
  "confidence": "medium",
  "copyright_status": "analysis-copy-only-or-reference-only"
}
```

使用以下状态：

- `complete`：取得可核验的逐字稿，并有标题或作者等上下文。
- `partial`：只有元数据、摘要、残缺逐字稿或少量画面信息；不得据此完成全文核验。
- `failed`：无法读取视频，或逐字稿与摘要均为空。

默认把元宝网页元数据结果的置信度设为 `low`。只有逐字稿能与视频可见字幕或用户提供材料交叉验证时才提高。视频号内容默认版权状态为 `reference-only`，除非权利人或许可证另有明确授权。

## 失败回退

按以下顺序回退，不循环尝试同一失败方式：

1. 请用户确认链接完整、内容仍公开可访问。
2. 请用户在微信中把视频转发给腾讯元宝，再复制其逐字稿回答。
3. 接受用户上传的原视频、录屏、字幕或关键截图。
4. 仅有标题和搜索摘要时停止，不进入“已核实”状态。

明确区分内容获取与事实核验：腾讯元宝只负责帮助读取视频，后续主张仍需按 `SKILL.md` 的证据优先级独立核实。
