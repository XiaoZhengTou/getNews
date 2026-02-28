# getNews

多平台热门内容 AI 日报工具，自动抓取 GitHub、抖音、小红书等平台热门内容，用 Claude AI 生成摘要，并发送到邮箱。

## 功能

- 抓取 GitHub 热门 AI 项目（含 README 详情）
- Claude AI 自动生成中文摘要
- 发送 HTML 格式邮件日报
- 支持定时调度（每天 09:00）
- 插件式架构，轻松扩展新平台

## 支持平台

| 平台 | 参数 | 状态 |
|------|------|------|
| GitHub 热门项目 | `github` | ✅ 真实数据 |
| 抖音热门内容 | `douyin` | 🔸 Mock 占位 |
| 小红书热门内容 | `xiaohongshu` | 🔸 Mock 占位 |

## 安装

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

```ini
GITHUB_TOKEN=your_github_token
EMAIL_FROM=your_email@qq.com
EMAIL_PASSWORD=your_email_auth_code
EMAIL_TO=recipient@example.com
ANTHROPIC_AUTH_TOKEN=your_claude_api_key
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选，默认官方地址
```

## 使用

```bash
# 抓取 GitHub 热门，发邮件
python main.py --platform github

# 指定条数，仅预览不发邮件
python main.py --platform github --count 3 --no-email

# 全平台合并日报
python main.py --platform all

# 多平台指定
python main.py --platform github,douyin

# 启动定时任务（每天 09:00 自动运行）
python main.py --platform all --schedule
```

## 扩展新平台

在 `fetchers/` 目录新建 `xxx_fetcher.py`，继承 `BaseFetcher` 并实现 `fetch()` 方法，设置 `platform_name` 即可自动注册，无需修改其他代码。

详见 [skills/fetch-hot.md](skills/fetch-hot.md)。

## 项目结构

```
├── main.py              # 入口，参数解析与调度
├── summarizer.py        # Claude AI 摘要生成
├── email_sender.py      # HTML 邮件发送
├── fetchers/            # 各平台抓取器
│   ├── base.py          # 基类与数据结构
│   ├── github_fetcher.py
│   ├── douyin_fetcher.py
│   └── xiaohongshu_fetcher.py
├── skills/              # Claude Code 技能
│   └── fetch-hot.md
├── requirements.txt
└── .env.example
```
