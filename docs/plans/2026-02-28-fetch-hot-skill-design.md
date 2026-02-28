# Design: 通用热门内容抓取 Skill（方案 A）

**日期：** 2026-02-28
**目标：** 将现有 GitHub 热门 AI 项目日报封装为可扩展的通用平台 Skill，后期支持抖音、小红书等主流平台。

---

## 一、整体架构

```
AiNews/
├── fetchers/
│   ├── __init__.py              ← 自动发现并注册所有 fetcher
│   ├── base.py                  ← BaseFetcher 抽象类 + HotItem 数据类
│   ├── github_fetcher.py        ← 现有逻辑迁移，继承 BaseFetcher
│   ├── douyin_fetcher.py        ← Mock 占位，待接入真实 API
│   └── xiaohongshu_fetcher.py   ← Mock 占位，待接入真实 API
├── skills/
│   └── fetch-hot.md             ← Claude Skill 文件：协议 + 提示词模板
├── summarizer.py                ← 改造：通用 HotItem → HTML，按平台切换提示词
├── email_sender.py              ← 改造：多平台内容分区混排
├── main.py                      ← 改造：--platform 参数，自动发现 fetchers
└── requirements.txt
```

### 数据流

```
/fetch-hot github
    → Skill 文件解析平台名
    → python main.py --platform github
    → fetchers/__init__.py 查 REGISTRY["github"]
    → GithubFetcher.fetch() 返回 List[HotItem]
    → summarizer.summarize_item() 按平台提示词总结
    → email_sender.send_email() 发送日报
```

---

## 二、BaseFetcher 接口

```python
# fetchers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

@dataclass
class HotItem:
    title: str        # 标题 / 热搜词
    url: str          # 链接（无则为空字符串）
    score: int        # 热度分（星数 / 播放量 / 搜索量）
    description: str  # 摘要（可为空）
    platform: str     # 来源平台名，如 "github" "douyin"
    is_mock: bool = field(default=False)  # 是否为 Mock 数据

class BaseFetcher(ABC):
    platform_name: str   # 子类必须声明，如 "github"
    platform_label: str  # 显示名，如 "GitHub" "抖音"

    @abstractmethod
    def fetch(self, count: int = 5) -> List[HotItem]:
        """返回热门内容列表"""
        ...

    def fetch_detail(self, item: HotItem) -> str:
        """获取详情文本（可选重写，默认返回空）"""
        return ""
```

---

## 三、Skill 文件设计（`skills/fetch-hot.md`）

### 手动触发协议

```
/fetch-hot [platform] [--count N] [--no-email]

支持平台：github | douyin | xiaohongshu | all

示例：
  /fetch-hot github              ← 抓 GitHub，发邮件
  /fetch-hot douyin --count 10   ← 抖音 Top10
  /fetch-hot all                 ← 全平台合并一封日报
  /fetch-hot github --no-email   ← 仅输出，不发邮件
```

### Python 定时调用

```bash
python main.py --platform github        # 单平台
python main.py --platform all           # 全平台
python main.py --platform github,douyin # 指定多平台
```

### 各平台提示词风格

| 平台 | 总结重点 |
|------|---------|
| github | AI 工具价值、上手难度、适用场景 |
| douyin | 内容趋势、爆款原因、创作者信息 |
| xiaohongshu | 种草逻辑、受众画像、关键词标签 |

---

## 四、summarizer & email_sender 改造

### summarizer.py

- 新增 `PROMPT_TEMPLATES: dict[str, str]` — 每平台一套提示词
- 新接口：`summarize_item(item: HotItem, detail: str = "") -> str`
- 根据 `item.platform` 选择对应模板，返回 HTML 片段

### email_sender.py

- `send_email()` 接收 `dict[str, List[tuple[HotItem, str]]]`（平台 → 条目列表）
- `build_html()` 按平台分区渲染，每区有平台图标和条数标注
- Mock 数据条目标注 `[Mock]` 标签

邮件布局示意：
```
🤖 AI 热门内容日报   2026-02-28 | 3个平台
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 GitHub  (5条)
  #1 ⭐12k  项目名 — 介绍...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎵 抖音  (5条) [Mock]
  #1 🔥980万  话题名 — 介绍...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📕 小红书  (5条) [Mock]
  #1 ❤️4.2万  帖子名 — 介绍...
```

---

## 五、错误处理 & Mock 策略

### Mock 占位规范

```python
class DouyinFetcher(BaseFetcher):
    platform_name = "douyin"
    platform_label = "抖音"

    def fetch(self, count=5) -> List[HotItem]:
        # TODO: 接入真实 API 后替换
        return [
            HotItem(title="AI绘画教程爆火", url="", score=9800000,
                    description="Mock数据", platform="douyin", is_mock=True),
        ]
```

### 错误处理原则

| 场景 | 处理方式 |
|------|---------|
| 某平台抓取失败 | 跳过该平台，其余正常发送，日志记录 |
| Claude 总结超时/失败 | 降级：直接用标题+描述拼 HTML |
| 邮件发送失败 | 抛出异常，打印内容到终端作备份 |

### 自动发现机制

`fetchers/__init__.py` 扫描目录，找所有继承 `BaseFetcher` 的类，按 `platform_name` 注册到 `REGISTRY`。新增平台只需新建一个 `xxx_fetcher.py`，无需修改其他代码。

---

## 六、扩展路线图

1. **现在**：GitHub（真实） + 抖音/小红书（Mock）
2. **下一步**：接入第三方 API（如 RapidAPI）替换 Mock
3. **未来**：微博热搜（有公开接口）、B站热门、知乎热榜
