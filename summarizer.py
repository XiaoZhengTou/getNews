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
