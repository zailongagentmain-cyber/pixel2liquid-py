"""
测试: cache.CacheManager
"""
import pytest
import tempfile
import os
from pathlib import Path
from pixel2liquid.cache import CacheManager


def test_cache_manager__init():
    """验证：创建缓存管理器"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        assert cache.base_domain == "www.fandomara.com"
        assert cache.cache_root == Path(tmpdir) / "www.fandomara.com"
        assert cache.pages_dir == Path(tmpdir) / "www.fandomara.com" / "pages"
        assert cache.assets_dir == Path(tmpdir) / "www.fandomara.com" / "assets"


def test_cache_manager__url_to_path():
    """验证：URL 转本地路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        # 首页
        assert cache._url_to_path("https://www.fandomara.com") == cache.pages_dir / "index.html"
        
        # collections
        path = cache._url_to_path("https://www.fandomara.com/collections/all")
        assert "collections" in str(path)
        assert str(path).endswith(".html")
        
        # products
        path = cache._url_to_path("https://www.fandomara.com/products/test")
        assert "products" in str(path)
        assert str(path).endswith(".html")


def test_cache_manager__trailing_slash():
    """验证：尾随斜杠统一处理（业务严丝合缝）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        # 有无尾随斜杠应该映射到同一个文件
        path1 = cache._url_to_path("https://www.fandomara.com")
        path2 = cache._url_to_path("https://www.fandomara.com/")
        
        assert path1 == path2
        assert str(path1).endswith("index.html")
        
        # 保存后，两个 URL 都能读取
        html = "<html>Test</html>"
        cache.save_page("https://www.fandomara.com", html)
        
        assert cache.has_page("https://www.fandomara.com")
        assert cache.has_page("https://www.fandomara.com/")
        assert cache.load_page("https://www.fandomara.com") == html
        assert cache.load_page("https://www.fandomara.com/") == html
        
        # 规范化 URL 验证
        norm1 = cache._normalize_url_for_key("https://www.fandomara.com")
        norm2 = cache._normalize_url_for_key("https://www.fandomara.com/")
        assert norm1 == norm2


def test_cache_manager__save_and_load_page():
    """验证：保存和加载页面"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        url = "https://www.fandomara.com/collections/all"
        html = "<html><body>Test Page</body></html>"
        
        # 保存
        normalized_url, saved_path = cache.save_page(url, html)
        assert Path(saved_path).exists()
        assert "www.fandomara.com" in normalized_url
        
        # 加载
        loaded = cache.load_page(url)
        assert loaded == html


def test_cache_manager__has_page():
    """验证：检查页面是否已缓存"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        url = "https://www.fandomara.com/collections/all"
        html = "<html><body>Test</body></html>"
        
        assert not cache.has_page(url)
        
        cache.save_page(url, html)
        
        assert cache.has_page(url)


def test_cache_manager__save_and_load_state():
    """验证：保存和加载爬取状态"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        state = {
            "start_url": "https://www.fandomara.com",
            "visited_count": 10,
            "pages": {}
        }
        
        # 保存
        cache.save_state(state)
        assert cache.state_file.exists()
        
        # 加载
        loaded = cache.load_state()
        assert loaded["start_url"] == "https://www.fandomara.com"
        assert loaded["visited_count"] == 10


def test_cache_manager__save_and_load_manifest():
    """验证：保存和加载资源清单"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        manifest = {
            "https://cdn.shopify.com/style.css": "assets/css/style.css",
            "https://cdn.shopify.com/script.js": "assets/js/script.js",
        }
        
        # 保存
        cache.save_manifest(manifest)
        assert cache.manifest_file.exists()
        
        # 加载
        loaded = cache.load_manifest()
        assert len(loaded) == 2
        assert "https://cdn.shopify.com/style.css" in loaded


def test_cache_manager__get_cache_info():
    """验证：获取缓存信息"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        # 保存一个页面
        cache.save_page("https://www.fandomara.com", "<html>")
        
        info = cache.get_cache_info()
        
        assert info["pages_count"] == 1
        assert info["state_exists"] == False
        assert info["manifest_exists"] == False


def test_cache_manager__clear():
    """验证：清除缓存"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager("https://www.fandomara.com", tmpdir)
        
        # 保存数据
        cache.save_page("https://www.fandomara.com", "<html>")
        cache.save_state({"test": "data"})
        
        assert cache.pages_dir.exists()
        assert cache.state_file.exists()
        
        # 清除
        cache.clear()
        
        # clear() 会删除整个目录然后重建空目录
        # 所以 pages 目录应该存在但为空
        assert cache.pages_dir.exists()
        assert list(cache.pages_dir.rglob('*')) == []
