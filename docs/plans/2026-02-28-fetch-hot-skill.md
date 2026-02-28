# Fetch-Hot Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有 GitHub 热门 AI 项目日报重构为可扩展的多平台通用 Skill，通过 BaseFetcher 插件机制支持抖音、小红书等平台（Mock 占位），并提供 Claude Skill 文件供手动触发。

**Architecture:** 每个平台是一个继承 `BaseFetcher` 的 Python 文件，放入 `fetchers/` 目录后自动注册。`summarizer.py` 按 `platform_name` 选择对应提示词模板。`email_sender.py` 按平台分区渲染邮件。`skills/fetch-hot.md` 定义 Claude 手动触发协议。

**Tech Stack:** Python 3.x, anthropic SDK, requests, python-dotenv, schedule, abc/dataclasses (标准库)

---

### Task 1: 创建 fetchers/base.py — HotItem + BaseFetcher

**Files:**
- Create: `fetchers/base.py`
- Create: `fetchers/__init__.py`（空文件，标记 package）

**Step 1: 创建 `fetchers/` 目录并写 `base.py`**

```python
# fetchers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class HotItem:
    title: str
    url: str
    score: int
    description: str
    platform: str
    is_mock: bool = field(default=False)


class BaseFetcher(ABC):
    platform_name: str   # 子类必须声明，如 "github"
    platform_label: str  # 显示名，如 "GitHub" "抖音"

    @abstractmethod
    def fetch(self, count: int = 5) -> List[HotItem]:
        """返回热门内容列表"""
        ...

    def fetch_detail(self, item: "HotItem") -> str:
        """获取详情文本（可选重写，默认返回空）"""
        return ""
```

**Step 2: 创建空 `fetchers/__init__.py`**

```python
# fetchers/__init__.py
```

**Step 3: 手动验证（无 pytest）**

```bash
cd d:/job/AiNews
python -c "from fetchers.base import HotItem, BaseFetcher; print('OK')"
```

Expected output: `OK`

**Step 4: Commit**

```bash
git init  # 如果还没有 git repo
git add fetchers/base.py fetchers/__init__.py
git commit -m "feat: add HotItem dataclass and BaseFetcher abstract class"
```

---

### Task 2: 创建 fetchers/auto_registry.py — 自动发现机制

**Files:**
- Create: `fetchers/auto_registry.py`
- Modify: `fetchers/__init__.py`

**Step 1: 写自动发现逻辑**

```python
# fetchers/auto_registry.py
import importlib
import pkgutil
import inspect
from typing import Dict
from fetchers.base import BaseFetcher


def build_registry() -> Dict[str, BaseFetcher]:
    """扫描 fetchers/ 包，找所有 BaseFetcher 子类，按 platform_name 注册"""
    registry: Dict[str, BaseFetcher] = {}

    import fetchers as pkg
    for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
        if module_name in ("base", "auto_registry"):
            continue
        module = importlib.import_module(f"fetchers.{module_name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(cls, BaseFetcher)
                and cls is not BaseFetcher
                and hasattr(cls, "platform_name")
            ):
                registry[cls.platform_name] = cls()

    return registry
```

**Step 2: 在 `__init__.py` 暴露 REGISTRY**

```python
# fetchers/__init__.py
from fetchers.auto_registry import build_registry

REGISTRY = build_registry()

__all__ = ["REGISTRY"]
```

**Step 3: 验证（此时 registry 为空，因为还没有 fetcher 实现）**

```bash
python -c "from fetchers import REGISTRY; print('Registry:', REGISTRY)"
```

Expected: `Registry: {}`

**Step 4: Commit**

```bash
git add fetchers/auto_registry.py fetchers/__init__.py
git commit -m "feat: auto-discovery registry for BaseFetcher subclasses"
```

---

### Task 3: 迁移 github_fetcher.py → fetchers/github_fetcher.py

**Files:**
- Create: `fetchers/github_fetcher.py`（从现有 `github_fetcher.py` 改造）
- 现有 `github_fetcher.py` 暂时保留，最后删除

**Step 1: 写新的 `fetchers/github_fetcher.py`**

```python
# fetchers/github_fetcher.py
import os
import requests
from dotenv import load_dotenv
from typing import List
from fetchers.base import BaseFetcher, HotItem

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
KEYWORDS = ["claude", "ai", "developer", "frontend", "vscode",
            "tool", "assistant", "code", "productivity"]


class GithubFetcher(BaseFetcher):
    platform_name = "github"
    platform_label = "GitHub"

    def fetch(self, count: int = 5) -> List[HotItem]:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "ai developer tools stars:>500 pushed:>2025-01-01",
            "sort": "updated",
            "order": "desc",
            "per_page": count * 3,
        }
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get("items", [])

        filtered = []
        for r in items:
            desc = (r.get("description") or "").lower()
            name = r["name"].lower()
            if any(kw in desc or kw in name for kw in KEYWORDS):
                filtered.append(HotItem(
                    title=r["name"],
                    url=r["html_url"],
                    score=r["stargazers_count"],
                    description=r.get("description", ""),
                    platform="github",
                ))
            if len(filtered) >= count:
                break

        return filtered[:count]

    def fetch_detail(self, item: HotItem) -> str:
        """获取 README 内容"""
        parts = item.url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        headers = {**HEADERS, "Accept": "application/vnd.github.raw"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 404:
            return ""
        res.raise_for_status()
        return res.text
```

**Step 2: 验证注册成功**

```bash
python -c "from fetchers import REGISTRY; print('Registry:', list(REGISTRY.keys()))"
```

Expected: `Registry: ['github']`

**Step 3: Commit**

```bash
git add fetchers/github_fetcher.py
git commit -m "feat: migrate GithubFetcher to BaseFetcher plugin"
```

---

### Task 4: 创建 Mock fetcher — 抖音 & 小红书

**Files:**
- Create: `fetchers/douyin_fetcher.py`
- Create: `fetchers/xiaohongshu_fetcher.py`

**Step 1: 写 `fetchers/douyin_fetcher.py`**

```python
# fetchers/douyin_fetcher.py
from typing import List
from fetchers.base import BaseFetcher, HotItem


class DouyinFetcher(BaseFetcher):
    platform_name = "douyin"
    platform_label = "抖音"

    def fetch(self, count: int = 5) -> List[HotItem]:
        # TODO: 接入真实 API 后替换此处 Mock 数据
        mock_data = [
            HotItem(title="AI绘画教程爆火全网", url="", score=9800000,
                    description="UP主用 AI 工具一键生成国风插画，单视频播放破千万", platform="douyin", is_mock=True),
            HotItem(title="程序员转行AI提示词工程师", url="", score=6500000,
                    description="分享从码农到 AI Prompt Engineer 的转型经历", platform="douyin", is_mock=True),
            HotItem(title="ChatGPT替代品测评", url="", score=5200000,
                    description="国内可用的5款免费 AI 助手横向对比", platform="douyin", is_mock=True),
            HotItem(title="AI配音神器来了", url="", score=4800000,
                    description="10秒克隆声音，视频配音再也不用花钱", platform="douyin", is_mock=True),
            HotItem(title="老板用AI替代了3个员工", url="", score=4100000,
                    description="揭秘中小企业正在偷偷用的AI工具", platform="douyin", is_mock=True),
        ]
        return mock_data[:count]
```

**Step 2: 写 `fetchers/xiaohongshu_fetcher.py`**

```python
# fetchers/xiaohongshu_fetcher.py
from typing import List
from fetchers.base import BaseFetcher, HotItem


class XiaohongshuFetcher(BaseFetcher):
    platform_name = "xiaohongshu"
    platform_label = "小红书"

    def fetch(self, count: int = 5) -> List[HotItem]:
        # TODO: 接入真实 API 后替换此处 Mock 数据
        mock_data = [
            HotItem(title="我用AI帮我写完了所有周报", url="", score=42000,
                    description="附提示词模板，打工人必收藏", platform="xiaohongshu", is_mock=True),
            HotItem(title="Claude vs GPT-4 深度测评", url="", score=38000,
                    description="用了三个月两款产品，说说真实感受", platform="xiaohongshu", is_mock=True),
            HotItem(title="AI画出我的梦中情房", url="", score=31000,
                    description="MidJourney 室内设计提示词分享，附效果图", platform="xiaohongshu", is_mock=True),
            HotItem(title="在家兼职AI数据标注月入8000", url="", score=27000,
                    description="真实经历分享，附接单平台推荐", platform="xiaohongshu", is_mock=True),
            HotItem(title="用Notion AI管理我的副业", url="", score=21000,
                    description="模板分享+工作流拆解，效率翻倍", platform="xiaohongshu", is_mock=True),
        ]
        return mock_data[:count]
```

**Step 3: 验证三个平台全部注册**

```bash
python -c "from fetchers import REGISTRY; print('Registry:', list(REGISTRY.keys()))"
```

Expected: `Registry: ['github', 'douyin', 'xiaohongshu']`（顺序可能不同）

**Step 4: Commit**

```bash
git add fetchers/douyin_fetcher.py fetchers/xiaohongshu_fetcher.py
git commit -m "feat: add Douyin and Xiaohongshu mock fetchers"
```

---

### Task 5: 改造 summarizer.py — 通用 HotItem 提示词模板

**Files:**
- Modify: `summarizer.py`

**Step 1: 替换 `summarizer.py` 全部内容**

```python
# summarizer.py
import os
import anthropic
from dotenv import load_dotenv
from fetchers.base import HotItem

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
)

PROMPT_TEMPLATES = {
    "github": """你是一个专注于 AI 开发工具的技术内容编辑。请根据以下 GitHub 项目信息，用中文写一段适合邮件阅读的项目介绍。

项目名：{title}
项目地址：{url}
Star 数：{score}
简介：{description}

详情（README 前8000字）：
{detail}

请输出以下结构（HTML 标签格式化）：
1. <h2>项目名称 + 一句话介绍</h2>
2. <p><strong>核心 AI 提效功能</strong>（3-5点，用 <ul><li> 列表）</p>
3. <p><strong>适用场景</strong></p>
4. <p><strong>快速上手</strong>（如有）</p>
5. <a href="{url}">查看项目 →</a>

风格：简洁专业，突出实用价值，重点关注开发效率提升和 AI 辅助能力。""",

    "douyin": """你是一个短视频内容分析师。请根据以下抖音热门内容，用中文写一段适合邮件阅读的趋势分析。

标题：{title}
播放量：{score:,}
简介：{description}

请输出以下结构（HTML 标签格式化）：
1. <h2>内容标题 + 一句话定性</h2>
2. <p><strong>爆款原因分析</strong>（2-3点，用 <ul><li>）</p>
3. <p><strong>内容趋势洞察</strong>（对创作者/从业者的启示）</p>

风格：分析客观，语言活泼，提炼规律而非描述现象。""",

    "xiaohongshu": """你是一个消费趋势分析师。请根据以下小红书热门内容，用中文写一段适合邮件阅读的种草趋势分析。

标题：{title}
点赞数：{score:,}
简介：{description}

请输出以下结构（HTML 标签格式化）：
1. <h2>内容标题 + 一句话定性</h2>
2. <p><strong>种草逻辑</strong>（为什么这条内容能打动人，2-3点，<ul><li>）</p>
3. <p><strong>受众画像</strong></p>
4. <p><strong>关键词标签</strong>（用 <code> 标签包裹，3-5个）</p>

风格：洞察精准，语言亲切，对内容创作者有参考价值。""",
}

DEFAULT_PROMPT = """请用中文简要介绍以下内容：
标题：{title}
简介：{description}
热度：{score}

用 <h2> 包裹标题，<p> 包裹正文，输出 HTML 格式。"""


def summarize_item(item: HotItem, detail: str = "") -> str:
    """根据平台选择提示词模板，返回 HTML 片段"""
    template = PROMPT_TEMPLATES.get(item.platform, DEFAULT_PROMPT)
    prompt = template.format(
        title=item.title,
        url=item.url or "#",
        score=item.score,
        description=item.description,
        detail=detail[:8000] if detail else "（无详情）",
    )

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        for block in message.content:
            if hasattr(block, "text"):
                return block.text
    except Exception as e:
        print(f"  [summarizer] Claude 调用失败，降级处理: {e}")
        # 降级：直接用标题+描述拼 HTML
        return f"<h2>{item.title}</h2><p>{item.description}</p>"

    return f"<h2>{item.title}</h2><p>{item.description}</p>"


# 保留旧接口兼容（供过渡期使用）
def summarize_for_email(repo_info: dict, readme_content: str) -> str:
    item = HotItem(
        title=repo_info["name"],
        url=repo_info["url"],
        score=repo_info["stars"],
        description=repo_info.get("description", ""),
        platform="github",
    )
    return summarize_item(item, detail=readme_content)
```

**Step 2: 验证导入**

```bash
python -c "from summarizer import summarize_item; print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add summarizer.py
git commit -m "feat: refactor summarizer with per-platform prompt templates"
```

---

### Task 6: 改造 email_sender.py — 多平台分区布局

**Files:**
- Modify: `email_sender.py`

**Step 1: 替换 `email_sender.py` 全部内容**

```python
# email_sender.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from fetchers.base import HotItem

load_dotenv()

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

PLATFORM_ICONS = {
    "github": "📦",
    "douyin": "🎵",
    "xiaohongshu": "📕",
}

PLATFORM_LABELS = {
    "github": "GitHub",
    "douyin": "抖音",
    "xiaohongshu": "小红书",
}


def build_platform_section(platform: str, items: List[Tuple[HotItem, str]]) -> str:
    icon = PLATFORM_ICONS.get(platform, "🔗")
    label = PLATFORM_LABELS.get(platform, platform)
    has_mock = any(item.is_mock for item, _ in items)
    mock_tag = ' <span style="color:#e36209;font-size:11px;">[Mock]</span>' if has_mock else ""

    items_html = ""
    for i, (item, content) in enumerate(items, 1):
        items_html += f"""
        <div style="margin-bottom:32px; border-left:4px solid #0366d6; padding-left:16px;">
            <p style="color:#586069; font-size:13px;">#{i} &nbsp; 热度 {item.score:,}</p>
            {content}
        </div>
        <hr style="border:none; border-top:1px solid #eee;">
        """

    return f"""
    <div style="margin-bottom:48px;">
        <h2 style="color:#24292e; border-bottom:2px solid #0366d6; padding-bottom:8px;">
            {icon} {label}{mock_tag}
            <span style="font-size:14px; font-weight:normal; color:#586069;">（{len(items)} 条）</span>
        </h2>
        {items_html}
    </div>
    """


def build_html(data: Dict[str, List[Tuple[HotItem, str]]]) -> str:
    """data: {platform_name: [(HotItem, html_summary), ...]}"""
    today = date.today().strftime("%Y-%m-%d")
    total = sum(len(v) for v in data.values())
    platform_count = len(data)

    sections_html = ""
    for platform, items in data.items():
        sections_html += build_platform_section(platform, items)

    return f"""
    <html><body style="font-family:Arial,sans-serif; max-width:700px; margin:auto; color:#24292e;">
        <h1 style="color:#0366d6;">🤖 AI 热门内容日报</h1>
        <p style="color:#586069;">{today} &nbsp;|&nbsp; {platform_count} 个平台 &nbsp;|&nbsp; 共 {total} 条</p>
        <hr style="border:none; border-top:2px solid #0366d6;">
        {sections_html}
        <p style="color:#999; font-size:12px;">由 Claude + 多平台数据自动生成</p>
    </body></html>
    """


def send_email(data: Dict[str, List[Tuple[HotItem, str]]], subject: str = None):
    """发送 HTML 日报邮件"""
    today = date.today().strftime("%Y-%m-%d")
    if subject is None:
        platforms = " + ".join(
            PLATFORM_LABELS.get(p, p) for p in data.keys()
        )
        subject = f"AI 热门内容日报 [{platforms}] {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    html = build_html(data)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"邮件已发送至 {EMAIL_TO}")
    except Exception as e:
        print(f"邮件发送失败: {e}")
        print("--- 日报内容（备份输出）---")
        for platform, items in data.items():
            print(f"\n[{platform}]")
            for item, _ in items:
                print(f"  - {item.title} (热度: {item.score:,})")
        raise
```

**Step 2: 验证导入**

```bash
python -c "from email_sender import build_html; print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add email_sender.py
git commit -m "feat: refactor email_sender to support multi-platform sections"
```

---

### Task 7: 改造 main.py — --platform 参数 + 通用流程

**Files:**
- Modify: `main.py`
- Delete: `github_fetcher.py`（旧文件，已被 fetchers/github_fetcher.py 替代）

**Step 1: 替换 `main.py`**

```python
# main.py
import argparse
import schedule
import time
from fetchers import REGISTRY
from summarizer import summarize_item
from email_sender import send_email


def run(platforms: list[str], count: int = 5, no_email: bool = False):
    """抓取指定平台热门内容并发送日报"""
    if "all" in platforms:
        platforms = list(REGISTRY.keys())

    data = {}  # {platform: [(HotItem, summary), ...]}

    for platform in platforms:
        if platform not in REGISTRY:
            print(f"[警告] 未知平台: {platform}，跳过。支持: {list(REGISTRY.keys())}")
            continue

        fetcher = REGISTRY[platform]
        print(f"\n[{fetcher.platform_label}] 开始抓取...")

        try:
            items = fetcher.fetch(count=count)
        except Exception as e:
            print(f"  抓取失败，跳过: {e}")
            continue

        print(f"  获取到 {len(items)} 条")
        summaries = []
        for item in items:
            print(f"  处理: {item.title[:40]}")
            try:
                detail = fetcher.fetch_detail(item)
                summary = summarize_item(item, detail=detail)
            except Exception as e:
                print(f"    总结失败，降级: {e}")
                summary = f"<h2>{item.title}</h2><p>{item.description}</p>"
            summaries.append((item, summary))

        data[platform] = summaries

    if not data:
        print("没有可发送的内容")
        return

    if no_email:
        print("\n[--no-email] 跳过发送，内容预览：")
        for platform, items in data.items():
            print(f"\n=== {platform} ===")
            for item, _ in items:
                print(f"  - {item.title}")
        return

    send_email(data)


def main():
    parser = argparse.ArgumentParser(description="AI 热门内容日报")
    parser.add_argument(
        "--platform", "-p",
        default="github",
        help="平台名，逗号分隔，或 'all'。支持: github, douyin, xiaohongshu, all",
    )
    parser.add_argument("--count", "-c", type=int, default=5, help="每平台抓取条数")
    parser.add_argument("--no-email", action="store_true", help="不发邮件，仅输出预览")
    parser.add_argument("--schedule", action="store_true", help="启动定时任务（每天09:00）")
    args = parser.parse_args()

    platforms = [p.strip() for p in args.platform.split(",")]

    if args.schedule:
        run(platforms, args.count, args.no_email)
        schedule.every().day.at("09:00").do(run, platforms, args.count, args.no_email)
        print("定时任务已启动，每天 09:00 自动发送...")
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run(platforms, args.count, args.no_email)


if __name__ == "__main__":
    main()
```

**Step 2: 删除旧的 github_fetcher.py**

```bash
rm d:/job/AiNews/github_fetcher.py
```

**Step 3: 验证 --help**

```bash
python main.py --help
```

Expected: 显示 usage 和参数说明

**Step 4: 冒烟测试（Mock 数据，不发邮件）**

```bash
python main.py --platform douyin,xiaohongshu --no-email
```

Expected: 输出抖音和小红书各5条 Mock 数据标题，无报错

**Step 5: Commit**

```bash
git add main.py
git rm github_fetcher.py
git commit -m "feat: refactor main.py with --platform arg and universal run() flow"
```

---

### Task 8: 创建 skills/fetch-hot.md — Claude Skill 文件

**Files:**
- Create: `skills/fetch-hot.md`

**Step 1: 写 Skill 文件**

```markdown
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
```

**Step 2: Commit**

```bash
git add skills/fetch-hot.md
git commit -m "feat: add fetch-hot Claude Skill file"
```

---

### Task 9: 端到端验证

**Step 1: 全平台 Mock 冒烟测试**

```bash
python main.py --platform all --no-email
```

Expected: 输出 github + douyin + xiaohongshu 各5条，无报错

**Step 2: 单 GitHub 平台真实测试（需要配置 .env）**

```bash
python main.py --platform github --count 3 --no-email
```

Expected: 输出3个真实 GitHub 仓库名和 Claude 总结片段

**Step 3: 验证自动发现新平台**

```bash
python -c "
from fetchers import REGISTRY
print('已注册平台:', list(REGISTRY.keys()))
for name, fetcher in REGISTRY.items():
    items = fetcher.fetch(count=1)
    print(f'  {name}: {items[0].title[:30]}')
"
```

Expected: 列出所有平台并各打印一条内容

**Step 4: 最终 Commit**

```bash
git add .
git commit -m "chore: final cleanup and end-to-end verification"
```

---

## 文件变更总览

| 操作 | 文件 |
|------|------|
| 新建 | `fetchers/__init__.py` |
| 新建 | `fetchers/base.py` |
| 新建 | `fetchers/auto_registry.py` |
| 新建 | `fetchers/github_fetcher.py` |
| 新建 | `fetchers/douyin_fetcher.py` |
| 新建 | `fetchers/xiaohongshu_fetcher.py` |
| 新建 | `skills/fetch-hot.md` |
| 改造 | `summarizer.py` |
| 改造 | `email_sender.py` |
| 改造 | `main.py` |
| 删除 | `github_fetcher.py`（已迁移）|
