# CheckInformation/chiqing

面向短视频创作者和前沿科技使用者的 Codex Skill：核实文案、链接或视频里的事实主张，找到实操教程与延展素材，标记素材的下载和复用状态，并改写为可拍摄的中文口播稿。

> 这不是通用新闻调查工具，也不替代法律意见或专业尽调。

## 能解决什么

- 看见一条科技或商业短视频后，快速判断哪些内容真实、夸大、过时或无法证实。
- 从官方公告、帮助中心、原始资料和可信媒体中找到可引用依据。
- 区分“证据素材”“实操教程”“延展素材”和“风险反例”。
- 把“能下载”和“能剪进成片”分开标注，避免把公开视频误当作可商用素材。
- 将核验结果改写成适合中文短视频拍摄的口播稿。

## 支持的输入

| 输入 | 示例 |
|---|---|
| 文案 | “核实这篇AI产品口播，找教程并改成可拍版本。” |
| 链接 | “核实这个发布页的说法，并找能合法使用的演示素材。” |
| 视频 | “核实这条视频里的主张，找原始教程和扩展资料。” |

视频无法读取或没有可靠字幕时，Skill 会要求提供字幕、截图或原始文案，而不是根据标题猜测内容。

## 输出结构

1. 一句话结论
2. 事实核验表
3. 教程与延展素材清单
4. 素材版权与使用说明
5. 可直接拍摄的口播稿

## 安装

将此仓库克隆或下载到本地后，把整个 `check-information-chiqing` 文件夹放进你的 Codex Skills 目录：

```text
~/.codex/skills/check-information-chiqing/
```

重启或刷新 Codex 后调用：

```text
调用 check-information-chiqing，核实这篇内容，找对应教程与延展视频，并改成口播稿。
```

## 素材版权原则

Skill 为每条素材单独标记下载与复用状态：

- **可下载且可复用**：来源或许可证明确允许当前用途。
- **可下载，复用未证实**：可供个人核验，不应直接剪入成片。
- **仅链接参考**：可以观看学习，不下载、不交付。
- **不建议使用**：授权、肖像、隐私或安全风险不清楚。

官方账号、下载按钮、公开视频都不自动等于可商用或可二创。详细规则见 [版权标签规范](references/rights-labels.md)。

## 项目结构

```text
check-information-chiqing/
├── SKILL.md                 # Codex 核心工作流
├── agents/openai.yaml       # Codex 界面元数据
├── references/              # 版权等按需读取的规则
├── examples/                # 使用示例
├── evals/                   # 回归测试题与通过条件
├── CONTRIBUTING.md          # 贡献方式
├── CHANGELOG.md             # 版本记录
└── LICENSE                  # MIT License
```

## 贡献

欢迎提交：新的高质量案例、来源核验规则、版权判断改进、不同平台的口播模板，以及可复现的失败案例。提交前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

[MIT](LICENSE)

---

## English summary

`CheckInformation/chiqing` is a Codex Skill for Chinese short-form creators and frontier-tech users. It fact-checks scripts, links, or videos; finds tutorials and supporting media; labels download and reuse rights separately; and rewrites the result into a publishable Chinese talking-head script.
