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
