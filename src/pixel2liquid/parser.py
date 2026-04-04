"""
Parser Module - 页面结构解析
"""
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from typing import Optional


@dataclass
class ParsedPage:
    """页面解析结果"""
    url: str                          # 原始 URL
    absolute_url: str                # 绝对 URL
    title: Optional[str]             # <title>
    meta_description: Optional[str]  # <meta name="description">
    internal_links: list[str]        # 站内链接（绝对路径）
    external_links: list[str]         # 站外链接
    asset_links: dict[str, list[str]]  # 资源链接 {type: [urls]}
    raw_html: str                    # 原始 HTML


def parse_page(html: str, base_url: str) -> ParsedPage:
    """
    解析页面，提取链接和资源
    
    Args:
        html: 页面 HTML 内容
        base_url: 基础 URL（用于解析相对路径）
    
    Returns:
        ParsedPage: 包含解析结果
    """
    soup = BeautifulSoup(html, "lxml")
    
    # 提取 title
    title_tag = soup.find("title")
    title = title_tag.string.strip() if title_tag and title_tag.string else None
    
    # 提取 meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc.get("content", None) if meta_desc else None
    
    # 解析 base_url 获取域名
    parsed_base = urlparse(base_url)
    base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    # 提取所有链接
    internal_links: set[str] = set()
    external_links: set[str] = set()
    
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        # 跳过锚点和 JavaScript
        if href.startswith("#") or href.startswith("javascript:"):
            continue
        
        # 转换为绝对路径
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        
        # 判断是站内还是站外
        if parsed.netloc == parsed_base.netloc:
            internal_links.add(absolute)
        else:
            external_links.add(absolute)
    
    # 提取资源链接
    asset_links: dict[str, list[str]] = {
        "css": [],
        "js": [],
        "images": [],
        "fonts": [],
    }
    
    # <link rel="stylesheet" href="...">
    for link_tag in soup.find_all("link", rel=["stylesheet", "preload"]):
        href = link_tag.get("href", "")
        if href:
            absolute = urljoin(base_url, href)
            if href.endswith(".css") or "stylesheet" in link_tag.get("rel", []):
                asset_links["css"].append(absolute)
    
    # <script src="...">
    for script_tag in soup.find_all("script", src=True):
        src = script_tag["src"]
        absolute = urljoin(base_url, src)
        asset_links["js"].append(absolute)
    
    # <img src="...">
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src", "")
        if src:
            absolute = urljoin(base_url, src)
            asset_links["images"].append(absolute)
    
    # <img srcset="...">
    for img_tag in soup.find_all("img"):
        srcset = img_tag.get("srcset", "")
        if srcset:
            # srcset 可以包含多个 URL
            for part in srcset.split(","):
                url = part.strip().split()[0]
                if url:
                    absolute = urljoin(base_url, url)
                    asset_links["images"].append(absolute)
    
    # <link rel="preload" as="font" href="...">
    for link_tag in soup.find_all("link", rel="preload"):
        href = link_tag.get("href", "")
        as_type = link_tag.get("as", "")
        if href and as_type == "font":
            absolute = urljoin(base_url, href)
            asset_links["fonts"].append(absolute)
    
    # <source srcset="..."> - 响应式图片（<picture> 标签内）
    for source_tag in soup.find_all("source"):
        srcset = source_tag.get("srcset", "")
        if srcset:
            for part in srcset.split(","):
                url = part.strip().split()[0]
                if url:
                    absolute = urljoin(base_url, url)
                    asset_links["images"].append(absolute)
    
    # <meta property="og:image"> - 社交分享图
    for meta_tag in soup.find_all("meta", property="og:image"):
        content = meta_tag.get("content", "")
        if content:
            absolute = urljoin(base_url, content)
            asset_links["images"].append(absolute)
    
    # <link rel="icon"> - favicon
    for link_tag in soup.find_all("link", rel="icon"):
        href = link_tag.get("href", "")
        if href:
            absolute = urljoin(base_url, href)
            asset_links["images"].append(absolute)
    
    # <link rel="modulepreload"> - JS 模块预加载
    for link_tag in soup.find_all("link", rel="modulepreload"):
        href = link_tag.get("href", "")
        if href:
            absolute = urljoin(base_url, href)
            asset_links["js"].append(absolute)
    
    # 转换为列表并去重
    return ParsedPage(
        url=base_url,
        absolute_url=urljoin(base_url, "/"),
        title=title,
        meta_description=meta_description,
        internal_links=sorted(internal_links),
        external_links=sorted(external_links),
        asset_links={
            k: sorted(set(v)) for k, v in asset_links.items()
        },
        raw_html=html
    )
