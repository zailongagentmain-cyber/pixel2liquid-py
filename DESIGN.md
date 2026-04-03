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

---

## AssetClassifier（资源分类器）

**目的**: 分析资源列表，分类哪些需要下载、哪些跳过

**技术栈**: 
- Python 内置（分类逻辑）

**资源分类规则**:
| 来源 | 示例 | 处理方式 |
|------|------|----------|
| Shopify CDN | `cdn.shopify.com` | ✅ 本地化 |
| Google Fonts | `fonts.googleapis.com`, `fonts.gstatic.com` | ❌ 不下载 |
| 第三方 CDN | `assets.gemcommerce.com` | ✅ 本地化 |

**资源类型**:
| 类型 | 说明 |
|------|------|
| `css` | 样式表 |
| `js` | JavaScript |
| `images` | 图片 |
| `fonts` | 字体文件 |

**实现方式**: 
- 输入: `asset_links` 字典 `{"css": [...], "js": [...]} `
- 输出: 分类后的字典 `{"to_download": {...}, "skip": {...}}`
- 按域名和类型双重分类

**测试方式**: 
```bash
uv run python -c "from pixel2liquid.asset import AssetClassifier; ..."
```

**预期结论**: 资源正确分类，返回需要下载和跳过的列表

**状态**: 🔄 待实现

**日期**: 2026-04-03

---

## AssetDownloader（资源下载器）

**目的**: 异步并发下载资源，支持断点续传

**技术栈**: 
- `asyncio` + `aiohttp`（异步并发）

**防 OOM 措施**:
- 并发数限制（10-20 个同时）
- 单文件超时（30 秒）
- 流式写入（不占用内存）
- 总超时（整个任务 5 分钟）

**实现方式**: 
- `asyncio.Semaphore` 控制并发
- `aiohttp.ClientTimeout` 设置超时
- 流式写入 `resp.content.iter_chunked(8192)`
- 返回 manifest（URL → 本地路径 映射）

**测试方式**: 
```bash
uv run python -c "from pixel2liquid.asset import AssetDownloader; ..."
```

**预期结论**: 资源下载成功，manifest 正确

**状态**: 🔄 待实现

**日期**: 2026-04-03

---

## ManifestManager（清单管理器）

**目的**: 维护全局资源清单，支持增量更新

**技术栈**: 
- Python 内置 json

**manifest 格式**:
```json
{
  "version": "1.0",
  "site": "www.fandomara.com",
  "assets": {
    "cdn.shopify.com": {
      "type": "shopify_cdn",
      "local_dir": "assets/shopify",
      "files": {
        "base.css": {
          "url": "https://cdn.shopify.com/.../base.css",
          "local_path": "assets/shopify/base.css",
          "size": 12345,
          "status": "downloaded"
        }
      }
    },
    "fonts.googleapis.com": {
      "type": "google_fonts",
      "skip": true
    }
  },
  "pages": {
    "www.fandomara.com/collections/all": {
      "html_path": "pages/collections/all.html",
      "assets_used": ["base.css", ...],
      "localized": false
    }
  }
}
```

**实现方式**: 
- `save_manifest()` / `load_manifest()`
- 增量更新（不覆盖已有记录）
- 记录跳过原因

**测试方式**: 
```bash
uv run python -c "from pixel2liquid.asset import ManifestManager; ..."
```

**预期结论**: manifest 正确保存和加载

**状态**: 🔄 待实现

**日期**: 2026-04-03

---

## LinkLocalizer（链接本地化）

**目的**: 替换 HTML 中的资源引用为本地路径

**技术栈**: 
- `BeautifulSoup4`（HTML 解析）
- `cssutils`（CSS 解析，处理 url()）
- `re`（正则表达式）

**处理的引用类型**:
| HTML 元素 | 属性 | 处理 |
|-----------|------|------|
| `<link>` | `href` | → 本地路径 |
| `<script>` | `src` | → 本地路径 |
| `<img>` | `src` | → 本地路径 |
| `<source>` | `src` | → 本地路径 |
| CSS `@import` | url() | → 本地路径 |
| CSS `background` | url() | → 本地路径 |

**保留不变的**:
- Google Fonts 引用（`fonts.googleapis.com`）
- Shopify Liquid 语法（`{{ '...' | asset_url }}`）

**实现方式**: 
1. 使用 BeautifulSoup 替换 HTML 属性
2. 使用 cssutils 解析 CSS 中的 url()
3. 使用 manifest 进行 URL → 本地路径映射

**测试方式**: 
```bash
uv run python -c "from pixel2liquid.asset import LinkLocalizer; ..."
```

**预期结论**: HTML 中的资源引用正确替换为本地路径

**状态**: 🔄 待实现

**日期**: 2026-04-03

---

## PageRenderer（页面渲染器）

**目的**: 本地渲染测试，验证页面正常显示

**技术栈**: 
- Vercel 部署（远程测试）
- 或 `http.server`（本地快速测试）

**实现方式**: 
1. 生成本地化 HTML
2. 部署到 Vercel 或启动本地服务器
3. 截图验证或手动检查

**测试方式**: 
```bash
vercel deploy
# 或
python -m http.server 8080
```

**预期结论**: 页面样式正常加载

**状态**: 🔄 待实现

**日期**: 2026-04-03

---

*本文档持续更新*
