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

    def fetch_detail(self, item: "HotItem") -> str:
        """获取详情文本（可选重写，默认返回空）"""
        return ""
