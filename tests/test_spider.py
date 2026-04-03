"""
测试: spider.fetch_single_page()
"""
import pytest
from pixel2liquid.spider import fetch_single_page, FetchResult


def test_fetch_single_page__success__when_site_is_valid():
    """验证：成功获取主页 HTML"""
    result = fetch_single_page("https://www.fandomara.com")
    
    assert result is not None
    assert result.status_code == 200
    assert result.html is not None
    assert len(result.html) > 10000  # Shopify 主页 HTML 通常很大
    assert "<html" in result.html.lower()
    assert result.error is None


def test_fetch_single_page__returns_fetch_result():
    """验证：返回 FetchResult 对象"""
    result = fetch_single_page("https://www.fandomara.com")
    
    assert isinstance(result, FetchResult)
    assert result.url == "https://www.fandomara.com"
    assert result.status_code == 200
    assert result.html is not None
    assert result.content_type is not None


def test_fetch_single_page__failed__when_404():
    """验证：404 页面返回 None"""
    result = fetch_single_page("https://www.fandomara.com/this-page-not-exists-12345")
    
    assert result is None


def test_fetch_single_page__failed__when_invalid_url():
    """验证：无效 URL 返回 None"""
    result = fetch_single_page("https://this-domain-not-exist-12345.com")
    
    assert result is None


def test_fetch_single_page__with_custom_headers():
    """验证：可以传递自定义 headers"""
    result = fetch_single_page(
        "https://www.fandomara.com",
        headers={"Accept-Language": "en-US"}
    )
    
    assert result is not None
    assert result.status_code == 200
