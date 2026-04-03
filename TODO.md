# Pixel2Liquid-Py TODO

**最后更新**: 2026-04-03

---

## Phase 2: 资源本地化（讨论确定 2026-04-03）

### 目标
将页面的所有核心资源下载到本地，替换 HTML 中的引用

### 模块顺序
1. **AssetClassifier** - 资源分类（哪些下载/跳过）
2. **AssetDownloader** - 资源下载（异步并发）
3. **ManifestManager** - 清单管理（URL → 本地路径）
4. **LinkLocalizer** - 链接替换（HTML/CSS 中的引用）
5. **PageRenderer** - 页面渲染（Vercel 部署测试）

### 测试页面
`collections/all` - 产品集合页

### 资源分类规则
| 来源 | 处理 |
|------|------|
| `cdn.shopify.com` | ✅ 本地化 |
| `fonts.googleapis.com` | ❌ 不下载 |
| `assets.gemcommerce.com` | ✅ 本地化 |

### 防 OOM 措施
- 并发限制（10-20 个）
- 单文件超时（30s）
- 流式写入

### 设计文档
已更新 DESIGN.md

---

## Phase 1: 网页采集

### 已完成
- [x] `check_page_accessible()` - 检测页面可访问性 ✅ (2026-04-03)
- [x] `fetch_single_page()` - 获取单个页面 HTML ✅ (2026-04-03)

### 进行中
- [ ] `PageParser` - 页面结构解析，提取链接和资源 ✅ (2026-04-03)
- [ ] `CrawlState` - 爬取状态保存，断点续传 ✅ (2026-04-03)
- [ ] `SiteCrawler` - 流式爬取，每10页面反馈 ✅ (2026-04-03)
- [ ] `CacheManager` - 本地缓存管理，避免重复爬取 ✅ (2026-04-03)
- [x] **Phase 1 完整缓存** - 60页面元数据 + 59个HTML文件 ✅ (2026-04-03)
  - `cache/www.fandomara.com/crawl_state.json`
  - `cache/www.fandomara.com/pages/`

### 待完成
- [ ] 站内链接追踪（多页面）
- [ ] 资源下载
- [ ] 进度显示
- [ ] 单元测试

**验证标准**: 成功率 >95%

---

## Phase 2: 格式转换

- [ ] HTML 解析
- [ ] HTML → Liquid 转换
- [ ] 路径修复
- [ ] CDN URL 替换

---

## Phase 3: CDN 处理

- [ ] 资源去重
- [ ] URL 映射表
- [ ] Protocol-relative URL 修复

---

## Phase 4: Shopify 适配

- [ ] Shopify 主题结构生成
- [ ] 资源上传
- [ ] Shopify CLI 集成

---

## Phase 5: CLI 工具化

- [ ] Click/Typer CLI 框架
- [ ] 命令实现
- [ ] 帮助文档

---

## 项目初始化

- [x] 确定技术栈细节（httpx vs aiohttp）
- [x] 初始化 Python 项目（uv）
- [ ] 配置 black/ruff/mypy
- [x] 建立目录结构

---

## 已完成

| 日期 | 完成项 |
|------|--------|
| 2026-04-03 | 项目初始化 |
| 2026-04-03 | check_page_accessible() |
| 2026-04-03 | fetch_single_page() |
