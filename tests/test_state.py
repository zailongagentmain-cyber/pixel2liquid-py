"""
测试: state.CrawlState
"""
import pytest
import tempfile
import os
from pathlib import Path
from pixel2liquid.state import CrawlState, PageRecord


def test_crawl_state__create():
    """验证：创建新状态"""
    state = CrawlState.create(
        start_url="https://example.com",
        base_domain="example.com"
    )
    
    assert state.start_url == "https://example.com"
    assert state.base_domain == "example.com"
    assert state.pending_urls == {"https://example.com"}
    assert state.visited_count == 0


def test_crawl_state__add_page():
    """验证：添加页面记录"""
    state = CrawlState.create("https://example.com", "example.com")
    
    page_record = PageRecord(
        url="https://example.com",
        absolute_url="https://example.com/",
        status="parsed",
        title="Test",
        internal_links=["https://example.com/about"],
        external_links=[],
        asset_links={"css": [], "js": [], "images": [], "fonts": []},
        error=None,
        discovered_at="2026-04-03T00:00:00",
        parsed_at="2026-04-03T00:00:00",
    )
    
    state.add_page("https://example.com", page_record.to_dict())
    
    assert "https://example.com" in state.pages
    assert state.pages["https://example.com"]["title"] == "Test"


def test_crawl_state__mark_visited():
    """验证：标记已访问"""
    state = CrawlState.create("https://example.com", "example.com")
    state.pending_urls.add("https://example.com/about")
    
    state.mark_visited("https://example.com")
    
    assert "https://example.com" in state.visited_urls
    assert "https://example.com" not in state.pending_urls
    assert state.visited_count == 1


def test_crawl_state__mark_failed():
    """验证：标记失败"""
    state = CrawlState.create("https://example.com", "example.com")
    
    state.mark_failed("https://example.com", "Connection timeout")
    
    assert "https://example.com" in state.failed_urls
    assert state.failed_urls["https://example.com"] == "Connection timeout"
    assert state.failed_count == 1


def test_crawl_state__get_next():
    """验证：获取下一个 URL"""
    state = CrawlState.create("https://example.com", "example.com")
    state.pending_urls.add("https://example.com/about")
    
    next_url = state.get_next()
    
    assert next_url in ["https://example.com", "https://example.com/about"]
    assert state.get_pending_count() == 1


def test_crawl_state__save_and_load():
    """验证：保存和加载状态"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = f"{tmpdir}/state.json"
        
        # 创建状态
        state = CrawlState.create("https://example.com", "example.com")
        page_record = PageRecord(
            url="https://example.com",
            absolute_url="https://example.com/",
            status="parsed",
            title="Test Page",
            internal_links=["https://example.com/about"],
            external_links=[],
            asset_links={"css": [], "js": [], "images": [], "fonts": []},
            error=None,
            discovered_at="2026-04-03T00:00:00",
            parsed_at="2026-04-03T00:00:00",
        )
        state.add_page("https://example.com", page_record.to_dict())
        state.mark_visited("https://example.com")
        
        # 保存
        state.save(state_path)
        assert Path(state_path).exists()
        
        # 加载
        loaded = CrawlState.load(state_path)
        
        assert loaded.start_url == state.start_url
        assert loaded.base_domain == state.base_domain
        assert loaded.visited_count == state.visited_count
        assert "https://example.com" in loaded.pages


def test_crawl_state__load_or_create__create():
    """验证：load_or_create 创建新状态"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = f"{tmpdir}/state.json"
        
        state = CrawlState.load_or_create(state_path, "https://example.com")
        
        assert state.start_url == "https://example.com"
        assert state.base_domain == "example.com"


def test_crawl_state__load_or_create__load():
    """验证：load_or_create 加载已有状态"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = f"{tmpdir}/state.json"
        
        # 先创建并保存
        state1 = CrawlState.create("https://example.com", "example.com")
        state1.save(state_path)
        
        # 再加载
        state2 = CrawlState.load_or_create(state_path, "https://example.com")
        
        assert state2.start_url == "https://example.com"
        assert state2.visited_count == 0


def test_crawl_state__is_complete():
    """验证：完成判断"""
    state = CrawlState.create("https://example.com", "example.com")
    assert not state.is_complete()
    
    state.pending_urls.clear()
    assert state.is_complete()
