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
