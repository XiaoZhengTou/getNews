---
name: fetch-hot
description: 抓取各平台热门内容并生成 AI 日报邮件。支持 GitHub、抖音、小红书等平台。
---

# Fetch Hot — 多平台热门内容日报

## 触发格式

```
/fetch-hot [platform] [--count N] [--no-email]
```

**支持平台：**

| 参数 | 平台 | 数据状态 |
|------|------|---------|
| `github` | GitHub 热门 AI 项目 | ✅ 真实数据 |
| `douyin` | 抖音热门内容 | 🔸 Mock 占位 |
| `xiaohongshu` | 小红书热门内容 | 🔸 Mock 占位 |
| `all` | 全部平台 | — |

**示例：**

```bash
/fetch-hot github              # GitHub 日报，发邮件
/fetch-hot douyin --count 10   # 抖音 Top10
/fetch-hot all                 # 全平台合并日报
/fetch-hot github --no-email   # 仅预览，不发邮件
```

## 执行步骤

当用户触发此 Skill 时，按以下步骤执行：

1. 解析平台参数（默认 `github`）
2. 运行对应 Python 命令：
   ```bash
   python main.py --platform <platform> [--count N] [--no-email]
   ```
3. 观察输出，报告每平台抓取条数
4. 告知用户邮件发送结果

## 新增平台指南

要添加新平台（如微博、B站），只需：

1. 在 `fetchers/` 目录创建 `weibo_fetcher.py`
2. 继承 `BaseFetcher`，实现 `fetch()` 方法
3. 设置 `platform_name = "weibo"` 和 `platform_label = "微博"`
4. 在 `summarizer.py` 的 `PROMPT_TEMPLATES` 中添加对应提示词
5. 在 `email_sender.py` 的 `PLATFORM_ICONS` 和 `PLATFORM_LABELS` 中添加显示配置
6. 重启后自动注册，无需修改其他代码

## 定时调度

```bash
# 每天 09:00 自动运行（后台）
python main.py --platform all --schedule
```
