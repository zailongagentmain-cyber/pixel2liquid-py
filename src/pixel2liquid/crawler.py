"""
Crawler Module - 网站爬取

使用 CacheManager 确保 URL 规范化
"""
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .spider import fetch_single_page
from .parser import parse_page
from .cache import CacheManager


def crawl_site(
    start_url: str,
    output_dir: str = "cache",
    max_pages: int = None,
    delay: float = 0.5,
    verbose: bool = True,
) -> dict:
    """
    流式爬取网站，使用 CacheManager 管理缓存
    
    Args:
        start_url: 起始 URL
        output_dir: 缓存目录
        max_pages: 最大页面数（None = 不限制）
        delay: 请求间隔（秒）
        verbose: 是否打印进度
    
    Returns:
        dict: 爬取状态
    """
    # 创建缓存管理器
    cache = CacheManager(start_url, output_dir)
    
    # 初始化已访问和待处理集合
    visited = set()
    pending = {start_url}
    pages_data = {}
    
    # 加载已有状态
    existing_state = cache.load_state()
    if existing_state and existing_state.get('pages'):
        pages_data = existing_state['pages']
        visited = set(pages_data.keys())
        # 从已有页面提取未处理的链接
        for url, page_data in pages_data.items():
            for link in page_data.get('internal_links', []):
                normalized = normalize_url(link)
                if normalized and normalized not in visited:
                    pending.add(link)
    
    if verbose:
        print(f"🔍 开始爬取: {start_url}")
        print(f"📁 缓存目录: {cache.cache_root}")
        print(f"📊 已有页面: {len(visited)}")
        print(f"📊 待爬取: {len(pending)}")
        print("-" * 50)
    
    # 主循环
    while pending:
        # 检查最大页面数
        if max_pages and len(visited) >= max_pages:
            if verbose:
                print(f"\n✅ 达到最大页面数 ({max_pages})")
            break
        
        url = pending.pop()
        
        # 规范化 URL
        normalized = normalize_url(url)
        if not normalized:
            continue
        
        # 跳过已访问
        if normalized in visited:
            continue
        
        # 只处理站内链接
        parsed = urlparse(url)
        if parsed.netloc != cache.base_domain:
            continue
        
        if verbose:
            print(f"[{len(visited) + 1}] {normalized[:60]}...")
        
        try:
            # 获取 HTML
            result = fetch_single_page(url)
            if result is None:
                # 失败也记录
                pages_data[normalized] = {
                    'url': normalized,
                    'absolute_url': url,
                    'status': 'failed',
                    'title': None,
                    'internal_links': [],
                    'external_links': [],
                    'asset_links': {},
                    'local_path': None,
                    'error': 'fetch failed',
                    'discovered_at': datetime.now().isoformat(),
                    'parsed_at': None,
                }
                visited.add(normalized)
                if verbose:
                    print(f"  ❌ 获取失败")
                continue
            
            # 解析页面
            parsed_page = parse_page(result.html, url)
            
            # 保存 HTML
            _, local_path = cache.save_page(url, result.html)
            
            # 创建页面记录
            pages_data[normalized] = {
                'url': normalized,
                'absolute_url': parsed_page.absolute_url,
                'status': 'parsed',
                'title': parsed_page.title,
                'internal_links': parsed_page.internal_links,
                'external_links': parsed_page.external_links,
                'asset_links': parsed_page.asset_links,
                'local_path': local_path,
                'error': None,
                'discovered_at': datetime.now().isoformat(),
                'parsed_at': datetime.now().isoformat(),
            }
            visited.add(normalized)
            
            # 添加新发现的链接
            new_count = 0
            for link in parsed_page.internal_links:
                link_normalized = normalize_url(link)
                if link_normalized and link_normalized not in visited:
                    pending.add(link)
                    new_count += 1
            
            # 保存状态
            state_data = {
                'start_url': start_url,
                'base_domain': cache.base_domain,
                'pages': pages_data,
                'visited_count': len(visited),
                'pending_count': len(pending),
            }
            cache.save_state(state_data)
            
            if verbose:
                print(f"  ✅ | 链接: {len(parsed_page.internal_links)} | 新发现: {new_count} | 待爬: {len(pending)}")
            
        except Exception as e:
            pages_data[normalized] = {
                'url': normalized,
                'absolute_url': url,
                'status': 'failed',
                'title': None,
                'internal_links': [],
                'external_links': [],
                'asset_links': {},
                'local_path': None,
                'error': str(e),
                'discovered_at': datetime.now().isoformat(),
                'parsed_at': None,
            }
            visited.add(normalized)
            if verbose:
                print(f"  ❌ 错误: {e}")
        
        # 请求间隔
        if delay > 0:
            time.sleep(delay)
        
        # 每10个页面详细反馈
        if verbose and len(visited) % 10 == 0 and len(visited) > 0:
            success = sum(1 for p in pages_data.values() if p['status'] == 'parsed')
            failed = sum(1 for p in pages_data.values() if p['status'] == 'failed')
            print(f"\n📊 进度报告 ({len(visited)} 页面)")
            print(f"   成功: {success} | 失败: {failed}")
            print(f"   待爬取: {len(pending)}")
            print("-" * 50)
    
    # 最终状态
    success = sum(1 for p in pages_data.values() if p['status'] == 'parsed')
    failed = sum(1 for p in pages_data.values() if p['status'] == 'failed')
    
    if verbose:
        print("\n" + "=" * 50)
        print(f"📊 最终统计")
        print(f"   总页面: {len(pages_data)}")
        print(f"   成功: {success}")
        print(f"   失败: {failed}")
        print(f"   缓存目录: {cache.cache_root}")
    
    return {
        'start_url': start_url,
        'base_domain': cache.base_domain,
        'pages': pages_data,
        'visited_count': len(visited),
        'success_count': success,
        'failed_count': failed,
    }


def normalize_url(url: str) -> str:
    """
    规范化 URL
    
    处理规则：
    1. 移除协议
    2. 统一尾随斜杠
    3. 小写化
    
    Args:
        url: 原始 URL
        
    Returns:
        规范化后的 URL
    """
    parsed = urlparse(url)
    path = parsed.path
    
    # 处理尾随斜杠
    if path == '/' or path == '':
        path = ''
    elif path.endswith('/'):
        path = path.rstrip('/')
    
    # 组合：域名 + 路径（如果有查询参数也要加上）
    normalized = f"{parsed.netloc}{path}"
    
    # 如果有查询参数，加上
    if parsed.query:
        normalized = f"{normalized}?{parsed.query}"
    
    return normalized.lower()
