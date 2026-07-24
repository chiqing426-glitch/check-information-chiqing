# Contributing

English summary: Contributions should make this Skill more accurate, reproducible, or safer for media rights handling. Bilingual documentation is welcome, but do not submit private data, secrets, downloaded media, or copyrighted material without a clear license basis.

欢迎改进这个 Skill。贡献应帮助它更准确、更可复现，或更安全地处理素材版权。

## 可以贡献什么

- 新的测试案例：旧闻当新闻、功能已撤回、地区限制、价格变化、夸大宣传等。
- 更可靠的来源层级或版权判断规则。
- 针对文案、链接或视频输入的失败案例及修复建议。
- 不同短视频平台、受众或口播风格的模板。

## 提交原则

- 不提交用户隐私、未公开合同、账号凭证、客户数据或受版权限制的素材文件。
- 不提交真实 `TENCENTCLOUD_APPID`、`TENCENTCLOUD_SECRET_ID`、`TENCENTCLOUD_SECRET_KEY` 或任何长期密钥；只允许提交空变量名和用途说明。
- 案例必须提供可公开访问的来源链接、访问日期和预期判断。
- 不把“有下载按钮”写成“允许二创”；明确说明下载与复用的依据。
- 修改 `SKILL.md`、连接器或脚本后，运行：

```bash
bash scripts/run_tests.sh
```

## 风格

- 核心工作流保持简洁、可执行、无平台偏见。
- 事实与推断分开写；无法证实时明确说明。
- 中文说明优先，必要时补充简短英文。

## English Contribution Notes

- Keep the core workflow concise, executable, and platform-neutral.
- Separate verified facts from inference; say when something cannot be verified.
- Keep real credentials out of commits, examples, issues, and logs.
- When adding external media examples, label both download permission and reuse permission.
