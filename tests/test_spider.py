"""
测试: spider.check_page_accessible()
"""
import pytest
from pixel2liquid.spider import check_page_accessible, PageCheckResult


def test_check_page_accessible__success__when_site_is_valid():
    """验证：有效站点返回 accessible=True"""
    result = check_page_accessible("https://www.fandomara.com")
    
    assert result.accessible is True
    assert result.status_code == 200
    assert result.has_shopify is True
    assert result.html_length > 1000
    assert result.error is None


def test_check_page_accessible__success__with_https():
    """验证：HTTPS 站点正确处理"""
    result = check_page_accessible("https://www.fandomara.com")
    
    assert result.url == "https://www.fandomara.com"
    assert result.status_code == 200


def test_check_page_accessible__failed__when_404():
    """验证：404 页面返回 accessible=False"""
    result = check_page_accessible("https://www.fandomara.com/this-page-does-not-exist-12345")
    
    assert result.accessible is False
    assert result.status_code == 404


def test_check_page_accessible__failed__when_invalid_url():
    """验证：无效 URL 返回错误信息"""
    result = check_page_accessible("https://this-domain-definitely-does-not-exist-12345.com")
    
    assert result.accessible is False
    assert result.error is not None


def test_check_page_accessible__has_cf_detection():
    """验证：Cloudflare 检测"""
    result = check_page_accessible("https://www.fandomara.com")
    
    # fandomara.com 有 Cloudflare但未拦截
    assert isinstance(result.has_cf, bool)
