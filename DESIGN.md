# DESIGN.md - 功能设计文档

**目的**：记录每个功能的设计决策，包括功能目的、技术栈、测试方式、预期结论

---

## 如何添加新功能

每个新功能必须在此文档中创建条目，格式如下：

```markdown
## [功能名称]

**目的**: 
**技术栈**: 
**实现方式**: 
**测试方式**: 
**预期结论**: 
**状态**: 
**日期**: 
```

---

## check_page_accessible

**目的**: 检测页面是否可访问

**技术栈**: 
- httpx（HTTP 客户端）

**实现方式**: 
- 发送 GET 请求，检查状态码
- 检测 Cloudflare（cf-ray header）
- 检测 Shopify（x-shopify header）

**测试方式**: 
```bash
pytest tests/test_spider.py::test_check_page_accessible__success__when_site_is_valid -v
```

**预期结论**: 返回 PageCheckResult，accessible=True

**状态**: ✅ 已完成

**日期**: 2026-04-03

---

## fetch_single_page

**目的**: 获取单个页面 HTML

**技术栈**: 
- httpx（HTTP 客户端）

**实现方式**: 
- 发送 GET 请求，携带浏览器 UA
- 4xx 返回 None，5xx 抛异常
- 返回 FetchResult 对象

**测试方式**: 
```bash
pytest tests/test_spider.py::test_fetch_single_page__success__when_site_is_valid -v
```

**预期结论**: 返回 FetchResult，HTML 长度 > 10000

**状态**: ✅ 已完成

**日期**: 2026-04-03

---

## PageParser

**目的**: 解析页面结构，提取链接和资源

**技术栈**: 
- BeautifulSoup4 + lxml（HTML 解析）
- urllib.parse.urljoin（相对路径 → 绝对路径）

**实现方式**: 
- 使用 BeautifulSoup 解析 HTML
- CSS 选择器提取 `<a href>`、`<link>`、`<script src>`、`<img src>`
- urljoin 转换相对路径为绝对路径
- 分离站内链接和站外链接

**测试方式**: 
```bash
pytest tests/test_parser.py -v
```

**预期结论**: 返回 ParsedPage，包含 internal_links、external_links、asset_links

**状态**: ✅ 已完成

**日期**: 2026-04-03

---

## CrawlState

**目的**: 保存爬取状态，支持断点续传

**技术栈**: 
- Python 内置 json（状态序列化）
- dataclass

**实现方式**: 
- CrawlState 类保存 pages、pending_urls、visited_urls
- save() 方法每页面保存到 JSON 文件
- load_or_create() 类方法从 JSON 恢复或创建新状态
- 流式处理，内存中只保留 pending_urls 集合

**测试方式**: 
```bash
pytest tests/test_state.py -v
```

**预期结论**: 保存后能正确恢复状态，增量保存正常

**状态**: ✅ 已完成

**日期**: 2026-04-03

---

## SiteCrawler

**目的**: 流式爬取网站，每10个页面反馈进度

**技术栈**: 
- 使用 spider.fetch_single_page()
- 使用 parser.parse_page()
- 使用 state.CrawlState

**实现方式**: 
- 队列式广度优先遍历
- 每1个页面保存一次状态
- 每10个页面打印进度
- 内存中只保留 pending_urls 集合

**测试方式**: 
```bash
pytest tests/test_crawler.py -v
```

**预期结论**: 成功爬取多个页面，状态正确保存

**状态**: ✅ 已完成

**日期**: 2026-04-03

---

*本文档持续更新*
