"""
Spider Module - 页面采集
"""
import httpx
from dataclasses import dataclass


@dataclass
class FetchResult:
    """页面获取结果"""
    url: str
    status_code: int
    html: str
    headers: dict
    content_type: str | None
    error: str | None


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


def fetch_single_page(
    url: str,
    timeout: float = 30.0,
    headers: dict | None = None
) -> FetchResult | None:
    """
    获取单个页面 HTML
    
    Args:
        url: 页面 URL
        timeout: 超时时间（秒）
        headers: 可选的自定义 headers
    
    Returns:
        FetchResult: 包含 HTML、状态码、headers 等
        None: 页面不存在（4xx）或请求失败
    
    Raises:
        无异常，直接返回 None 表示失败
    """
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        default_headers.update(headers)
    
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            headers=default_headers,
            follow_redirects=True
        )
        
        # 4xx 返回 None（页面不存在）
        if 400 <= response.status_code < 500:
            return None
        
        # 5xx 抛异常（服务器错误）
        if response.status_code >= 500:
            raise httpx.HTTPStatusError(
                f"Server error: {response.status_code}",
                request=response.request,
                response=response
            )
        
        # 获取 content-type
        content_type = response.headers.get("content-type", "")
        
        return FetchResult(
            url=url,
            status_code=response.status_code,
            html=response.text,
            headers=dict(response.headers),
            content_type=content_type,
            error=None
        )
        
    except httpx.TimeoutException:
        return None
        
    except httpx.RequestError:
        return None
        
    except httpx.HTTPStatusError:
        return None


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
