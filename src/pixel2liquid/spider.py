"""
Spider Module - 页面采集
"""
import httpx
from dataclasses import dataclass


@dataclass
class PageCheckResult:
    """页面检测结果"""
    url: str
    accessible: bool
    status_code: int
    has_cf: bool
    has_shopify: bool
    html_length: int
    error: str | None


def check_page_accessible(url: str, timeout: float = 10.0) -> PageCheckResult:
    """
    检测页面是否可访问
    
    Args:
        url: 页面 URL
        timeout: 超时时间（秒）
    
    Returns:
        PageCheckResult: 包含检测结果
    """
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        status_code = response.status_code
        html_length = len(response.text)
        
        # 检测 Cloudflare
        has_cf = (
            "cf-ray" in response.headers or
            "cf-cache-status" in response.headers or
            "cloudflare" in response.headers.get("server", "").lower()
        )
        
        # 检测 Shopify
        has_shopify = (
            "x-shopify" in response.headers or
            "shopify" in response.headers.get("server", "").lower() or
            "cdn.shopify.com" in response.text
        )
        
        # 2xx 算成功，3xx/4xx/5xx 算失败
        accessible = 200 <= status_code < 300
        
        return PageCheckResult(
            url=url,
            accessible=accessible,
            status_code=status_code,
            has_cf=has_cf,
            has_shopify=has_shopify,
            html_length=html_length,
            error=None
        )
        
    except httpx.TimeoutException:
        return PageCheckResult(
            url=url,
            accessible=False,
            status_code=0,
            has_cf=False,
            has_shopify=False,
            html_length=0,
            error="Timeout"
        )
        
    except httpx.RequestError as e:
        return PageCheckResult(
            url=url,
            accessible=False,
            status_code=0,
            has_cf=False,
            has_shopify=False,
            html_length=0,
            error=f"RequestError: {e}"
        )
        
    except Exception as e:
        return PageCheckResult(
            url=url,
            accessible=False,
            status_code=0,
            has_cf=False,
            has_shopify=False,
            html_length=0,
            error=str(e)
        )
