"""
Cache Module - 本地缓存管理

目的：保存中间结果，避免重复爬取

缓存结构：
  <site>/
  ├── crawl_state.json      # 爬取状态（URL、链接、统计）
  ├── pages/                # 每个页面的 HTML
  │   ├── index.html
  │   ├── collections/
  │   │   └── all.html
  │   └── products/
  │       └── electronic-button-pin.html
  ├── assets/               # 资源映射
  │   ├── css/
  │   ├── js/
  │   ├── images/
  │   └── fonts/
  └── manifest.json         # 索引（URL → 文件路径映射）
"""
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional


class CacheManager:
    """
    本地缓存管理器
    
    用于保存爬取结果，下次可以直接读取而不需要重新爬取
    """
    
    def __init__(self, site_url: str, cache_dir: str = "cache"):
        """
        初始化缓存管理器
        
        Args:
            site_url: 网站 URL（如 https://www.fandomara.com）
            cache_dir: 缓存根目录
        """
        self.site_url = site_url.rstrip('/')
        self.base_domain = urlparse(self.site_url).netloc
        
        # 缓存根目录
        self.cache_root = Path(cache_dir) / self.base_domain
        self.pages_dir = self.cache_root / "pages"
        self.assets_dir = self.cache_root / "assets"
        self.manifest_file = self.cache_root / "manifest.json"
        self.state_file = self.cache_root / "crawl_state.json"
        
        # 确保目录存在
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """确保缓存目录结构存在"""
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.joinpath("css").mkdir(exist_ok=True)
        self.assets_dir.joinpath("js").mkdir(exist_ok=True)
        self.assets_dir.joinpath("images").mkdir(exist_ok=True)
        self.assets_dir.joinpath("fonts").mkdir(exist_ok=True)
    
    def _normalize_url(self, url: str) -> str:
        """
        规范化 URL，确保每个 URL 有唯一表示
        
        处理规则：
        1. 移除协议（http://, https://）
        2. 统一尾随斜杠（/ → 空字符串）
        3. 小写化
        
        Args:
            url: 原始 URL
            
        Returns:
            规范化后的 URL
        """
        parsed = urlparse(url)
        
        # 移除协议，获取路径
        path = parsed.path
        
        # 统一尾随斜杠：/ → 空字符串
        if path.endswith('/') and len(path) > 1:
            path = path.rstrip('/')
        
        # 组合：域名 + 路径
        normalized = f"{parsed.netloc}{path}"
        
        return normalized.lower()
    
    def _url_to_path(self, url: str) -> Path:
        """
        将 URL 转换为本地文件路径
        
        Args:
            url: 页面 URL
            
        Returns:
            本地文件路径
        """
        normalized = self._normalize_url(url)
        
        # 移除域名得到路径
        parsed = urlparse(url)
        path = parsed.path.lstrip('/')
        
        if not path or path == '/':
            path = "index.html"
        elif not path.endswith('.html'):
            path = path + ".html"
        
        # 处理查询参数
        if parsed.query:
            # 查询参数中的冒号会导致文件名问题
            safe_query = re.sub(r'[:=]', '_', parsed.query)
            path = path.replace('.html', f'_q{safe_query}.html')
        
        return self.pages_dir / path
    
    def _get_dir_for_url(self, url: str) -> str:
        """
        获取 URL 对应的目录分类
        
        Args:
            url: 页面 URL
            
        Returns:
            目录分类名（如 collections, products, blogs）
        """
        parsed = urlparse(url)
        path = parsed.path
        
        if '/collections/' in path:
            return 'collections'
        elif '/products/' in path:
            return 'products'
        elif '/blogs/' in path:
            return 'blogs'
        elif '/pages/' in path:
            return 'pages'
        else:
            return 'root'
    
    def save_page(self, url: str, html: str) -> tuple[str, str]:
        """
        保存页面 HTML 到本地
        
        Args:
            url: 页面 URL
            html: 页面 HTML 内容
            
        Returns:
            (规范化 URL, 保存的文件路径)
        """
        # 规范化 URL（去除尾随斜杠）
        normalized_url = self._normalize_url_for_key(url)
        
        file_path = self._url_to_path(normalized_url)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return normalized_url, str(file_path)
    
    def _normalize_url_for_key(self, url: str) -> str:
        """
        规范化 URL 作为状态字典的 key
        
        处理规则：
        1. 移除协议
        2. 统一尾随斜杠（/ → 空）
        3. 小写化
        
        Args:
            url: 原始 URL
            
        Returns:
            规范化后的 URL（不带协议，作为 key 使用）
        """
        parsed = urlparse(url)
        path = parsed.path
        
        # 统一尾随斜杠：/ 和 空 都表示首页
        if path == '/' or path == '':
            path = ''
        elif path.endswith('/'):
            path = path.rstrip('/')
        
        # 组合：域名 + 路径
        normalized = f"{parsed.netloc}{path}"
        
        return normalized.lower()
    
    def load_page(self, url: str) -> Optional[str]:
        """
        从本地加载页面 HTML
        
        Args:
            url: 页面 URL
            
        Returns:
            页面 HTML 内容，如果不存在返回 None
        """
        # 规范化 URL
        normalized_url = self._normalize_url_for_key(url)
        file_path = self._url_to_path(normalized_url)
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None
    
    def has_page(self, url: str) -> bool:
        """
        检查页面是否已缓存
        
        Args:
            url: 页面 URL
            
        Returns:
            True 如果已缓存
        """
        # 规范化 URL
        normalized_url = self._normalize_url_for_key(url)
        file_path = self._url_to_path(normalized_url)
        return file_path.exists()
    
    def save_state(self, state_data: dict):
        """
        保存爬取状态
        
        Args:
            state_data: 爬取状态字典
        """
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    
    def load_state(self) -> Optional[dict]:
        """
        加载爬取状态
        
        Returns:
            爬取状态字典，如果不存在返回 None
        """
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save_manifest(self, manifest_data: dict):
        """
        保存资源映射清单
        
        Args:
            manifest_data: 资源映射字典
        """
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    
    def load_manifest(self) -> Optional[dict]:
        """
        加载资源映射清单
        
        Returns:
            资源映射字典，如果不存在返回 None
        """
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_cache_info(self) -> dict:
        """
        获取缓存信息
        
        Returns:
            缓存统计信息
        """
        info = {
            'cache_root': str(self.cache_root),
            'pages_count': 0,
            'assets_count': {},
            'state_exists': self.state_file.exists(),
            'manifest_exists': self.manifest_file.exists(),
        }
        
        # 统计页面数
        if self.pages_dir.exists():
            info['pages_count'] = len(list(self.pages_dir.rglob('*.html')))
        
        # 统计资源数
        for asset_type in ['css', 'js', 'images', 'fonts']:
            type_dir = self.assets_dir / asset_type
            if type_dir.exists():
                info['assets_count'][asset_type] = len(list(type_dir.iterdir()))
        
        return info
    
    def clear(self):
        """清除所有缓存"""
        import shutil
        
        if self.cache_root.exists():
            shutil.rmtree(self.cache_root)
            self._ensure_dirs()
