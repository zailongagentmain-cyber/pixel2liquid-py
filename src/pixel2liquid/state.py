"""
State Module - 爬取状态管理
"""
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class PageRecord:
    """页面记录"""
    url: str
    absolute_url: str
    status: str  # "pending" | "parsed" | "failed"
    title: Optional[str]
    internal_links: list[str]
    external_links: list[str]
    asset_links: dict[str, list[str]]
    error: Optional[str]
    discovered_at: str
    parsed_at: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PageRecord":
        return cls(**data)


@dataclass
class CrawlState:
    """爬取状态"""
    start_url: str
    base_domain: str
    pages: dict[str, dict]  # url -> PageRecord.to_dict()
    pending_urls: set[str]
    visited_urls: set[str]
    failed_urls: dict[str, str]
    visited_count: int
    failed_count: int
    started_at: str
    last_updated: str

    def save(self, path: str):
        """保存状态到 JSON 文件"""
        data = {
            "start_url": self.start_url,
            "base_domain": self.base_domain,
            "pages": self.pages,
            "pending_urls": list(self.pending_urls),
            "visited_urls": list(self.visited_urls),
            "failed_urls": self.failed_urls,
            "visited_count": self.visited_count,
            "failed_count": self.failed_count,
            "started_at": self.started_at,
            "last_updated": datetime.now().isoformat(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "CrawlState":
        """从 JSON 文件加载状态"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            start_url=data["start_url"],
            base_domain=data["base_domain"],
            pages=data["pages"],
            pending_urls=set(data["pending_urls"]),
            visited_urls=set(data["visited_urls"]),
            failed_urls=data["failed_urls"],
            visited_count=data["visited_count"],
            failed_count=data["failed_count"],
            started_at=data["started_at"],
            last_updated=data["last_updated"],
        )

    @classmethod
    def create(cls, start_url: str, base_domain: str) -> "CrawlState":
        """创建新状态"""
        now = datetime.now().isoformat()
        return cls(
            start_url=start_url,
            base_domain=base_domain,
            pages={},
            pending_urls={start_url},
            visited_urls=set(),
            failed_urls={},
            visited_count=0,
            failed_count=0,
            started_at=now,
            last_updated=now,
        )

    @classmethod
    def load_or_create(cls, path: str, start_url: str) -> "CrawlState":
        """加载或创建状态"""
        if Path(path).exists():
            return cls.load(path)
        from urllib.parse import urlparse
        parsed = urlparse(start_url)
        base_domain = parsed.netloc
        return cls.create(start_url, base_domain)

    def add_page(self, url: str, page_record: dict):
        """添加页面记录"""
        self.pages[url] = page_record

    def mark_visited(self, url: str):
        """标记已访问"""
        if url in self.pending_urls:
            self.pending_urls.remove(url)
        self.visited_urls.add(url)
        self.visited_count += 1
        self.last_updated = datetime.now().isoformat()

    def mark_failed(self, url: str, error: str):
        """标记失败"""
        if url in self.pending_urls:
            self.pending_urls.remove(url)
        self.failed_urls[url] = error
        self.failed_count += 1
        self.last_updated = datetime.now().isoformat()

    def get_next(self) -> Optional[str]:
        """获取下一个待访问的 URL"""
        if self.pending_urls:
            return self.pending_urls.pop()
        return None

    def get_pending_count(self) -> int:
        """获取待访问数量"""
        return len(self.pending_urls)

    def get_total_discovered(self) -> int:
        """获取已发现页面数量"""
        return len(self.pages)

    def is_complete(self) -> bool:
        """是否已完成所有页面爬取"""
        return len(self.pending_urls) == 0
