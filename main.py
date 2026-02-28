# main.py
import argparse
import schedule
import time
from fetchers import REGISTRY
from summarizer import summarize_item
from email_sender import send_email


def run(platforms: list, count: int = 5, no_email: bool = False):
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
