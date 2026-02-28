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
                print(f"  - {item.title}")
        raise
