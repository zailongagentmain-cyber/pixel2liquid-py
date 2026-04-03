"""
测试: parser.parse_page()
"""
import pytest
from pixel2liquid.parser import parse_page, ParsedPage


# 测试用 HTML
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="This is a test page">
    <link rel="stylesheet" href="/assets/style.css">
    <link rel="preload" as="font" href="/fonts/test.woff2">
    <script src="/js/app.js"></script>
</head>
<body>
    <h1>Hello</h1>
    <a href="/about">About Us</a>
    <a href="/products/item">Product</a>
    <a href="https://external-site.com/page">External Link</a>
    <img src="/images/logo.png" alt="Logo">
    <img srcset="/images/logo-small.png 100w, /images/logo-large.png 200w" alt="Logo">
</body>
</html>
"""

BASE_URL = "https://example.com"


def test_parse_page__extracts_title():
    """验证：提取 <title> 标签"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert result.title == "Test Page"


def test_parse_page__extracts_meta_description():
    """验证：提取 meta description"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert result.meta_description == "This is a test page"


def test_parse_page__extracts_internal_links():
    """验证：提取站内链接"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert "https://example.com/about" in result.internal_links
    assert "https://example.com/products/item" in result.internal_links


def test_parse_page__extracts_external_links():
    """验证：提取站外链接"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert "https://external-site.com/page" in result.external_links


def test_parse_page__extracts_css_links():
    """验证：提取 CSS 链接"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert "https://example.com/assets/style.css" in result.asset_links["css"]


def test_parse_page__extracts_js_links():
    """验证：提取 JS 链接"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert "https://example.com/js/app.js" in result.asset_links["js"]


def test_parse_page__extracts_image_links():
    """验证：提取图片链接"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert "https://example.com/images/logo.png" in result.asset_links["images"]
    assert "https://example.com/images/logo-small.png" in result.asset_links["images"]
    assert "https://example.com/images/logo-large.png" in result.asset_links["images"]


def test_parse_page__extracts_font_links():
    """验证：提取字体链接"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert "https://example.com/fonts/test.woff2" in result.asset_links["fonts"]


def test_parse_page__handles_relative_urls():
    """验证：处理相对路径"""
    result = parse_page(SAMPLE_HTML, BASE_URL + "/subpage/")
    
    # ../about 应该在 base_url/subpage/ 的基础上解析
    assert len(result.internal_links) >= 2


def test_parse_page__returns_parsed_page():
    """验证：返回 ParsedPage 对象"""
    result = parse_page(SAMPLE_HTML, BASE_URL)
    
    assert isinstance(result, ParsedPage)
    assert result.url == BASE_URL
    assert result.absolute_url == BASE_URL + "/"


def test_parse_page__skips_anchors_and_js():
    """验证：跳过锚点和 JavaScript 链接"""
    html = '<a href="#section">Anchor</a><a href="javascript:void(0)">JS</a>'
    result = parse_page(html, BASE_URL)
    
    assert len(result.internal_links) == 0


def test_parse_page__fandomara_homepage():
    """验证：解析 fandomara.com 主页"""
    from pixel2liquid.spider import fetch_single_page
    
    result_fetch = fetch_single_page("https://www.fandomara.com")
    assert result_fetch is not None
    
    result = parse_page(result_fetch.html, result_fetch.url)
    
    assert result.title is not None
    assert len(result.internal_links) > 0
    assert len(result.external_links) > 0
    assert len(result.asset_links["css"]) > 0
    assert len(result.asset_links["js"]) > 0
    assert len(result.asset_links["images"]) > 0
