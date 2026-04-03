"""
Crawler Module - 网站爬取
"""
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .spider import fetch_single_page
from .parser import parse_page
from .state import CrawlState, PageRecord


def crawl_site(
    start_url: str,
    output_dir: str,
    state_file: str = "crawl_state.json",
    max_pages: int = None,
    delay: float = 0.5,
    verbose: bool = True,
) -> CrawlState:
    """
    流式爬取网站
    
    Args:
        start_url: 起始 URL
        output_dir: 输出目录
        state_file: 状态文件名
        max_pages: 最大页面数（None = 不限制）
        delay: 请求间隔（秒）
        verbose: 是否打印进度
    
    Returns:
        CrawlState: 最终爬取状态
    """
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    state_path = f"{output_dir}/{state_file}"
    
    # 加载或创建状态
    state = CrawlState.load_or_create(state_path, start_url)
    
    if verbose:
        print(f"🔍 开始爬取: {start_url}")
        print(f"📁 输出目录: {output_dir}")
        print(f"📊 初始待爬取: {len(state.pending_urls)}")
        print(f"📊 已访问: {state.visited_count}")
        print("-" * 50)
    
    # 主循环
    while True:
        # 检查是否完成
        if state.is_complete():
            if verbose:
                print(f"\n✅ 爬取完成！")
            break
        
        # 检查最大页面数
        if max_pages and state.visited_count >= max_pages:
            if verbose:
                print(f"\n✅ 达到最大页面数 ({max_pages})")
            break
        
        # 获取下一个 URL
        url = state.get_next()
        if not url:
            break
        
        # 跳过外部域名
        parsed = urlparse(url)
        if parsed.netloc != state.base_domain:
            continue
        
        # 获取页面
        if verbose:
            print(f"[{state.visited_count + 1}] 爬取: {url[:60]}...")
        
        try:
            # 获取 HTML
            fetch_result = fetch_single_page(url)
            if fetch_result is None:
                state.mark_failed(url, "fetch failed")
                if verbose:
                    print(f"  ❌ 获取失败")
                continue
            
            # 解析页面
            parsed_page = parse_page(fetch_result.html, url)
            
            # 创建页面记录
            page_record = PageRecord(
                url=url,
                absolute_url=parsed_page.absolute_url,
                status="parsed",
                title=parsed_page.title,
                internal_links=parsed_page.internal_links,
                external_links=parsed_page.external_links,
                asset_links=parsed_page.asset_links,
                error=None,
                discovered_at=datetime.now().isoformat(),
                parsed_at=datetime.now().isoformat(),
            )
            
            # 添加到状态
            state.add_page(url, page_record.to_dict())
            state.mark_visited(url)
            
            # 添加新发现的 URL
            new_urls = 0
            for link in parsed_page.internal_links:
                if link not in state.visited_urls and link not in state.pending_urls:
                    state.pending_urls.add(link)
                    new_urls += 1
            
            # 每1个页面保存状态
            state.save(state_path)
            
            if verbose:
                print(f"  ✅ 完成 | 链接: {len(parsed_page.internal_links)} | 资源: {sum(len(v) for v in parsed_page.asset_links.values())} | 新发现: {new_urls} | 待爬: {state.get_pending_count()}")
            
        except Exception as e:
            state.mark_failed(url, str(e))
            state.save(state_path)
            if verbose:
                print(f"  ❌ 错误: {e}")
        
        # 请求间隔
        if delay > 0:
            time.sleep(delay)
        
        # 每10个页面详细反馈
        if verbose and state.visited_count % 10 == 0 and state.visited_count > 0:
            print(f"\n📊 进度报告 ({state.visited_count} 页面)")
            print(f"   待爬取: {state.get_pending_count()}")
            print(f"   已访问: {state.visited_count}")
            print(f"   失败: {state.failed_count}")
            print(f"   总发现: {state.get_total_discovered()}")
            print("-" * 50)
    
    # 最终状态
    if verbose:
        print("\n" + "=" * 50)
        print(f"📊 最终统计")
        print(f"   总页面: {state.get_total_discovered()}")
        print(f"   已访问: {state.visited_count}")
        print(f"   失败: {state.failed_count}")
        print(f"   待爬取: {state.get_pending_count()}")
        print(f"   状态文件: {state_path}")
    
    return state
