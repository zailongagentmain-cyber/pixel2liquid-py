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

### ⚠️ 待完成：三模块衔接（重要）
- [ ] AssetClassifier → ManifestManager → AssetDownloader 衔接
- [ ] 实现断点续传：下载失败后重启能够继续
- [ ] 龙老板提醒：我会在三个模块开发完后执行此事

### 🔧 URL 本地化待修复（2026-04-04 新增）

#### PageParser 遗漏（源头问题）
- [ ] 添加 `meta[property="og:image"]` content 提取（P0）
- [ ] 添加 JS 对象 string value 中的 URL 扫描（PageFly/Parkour JSON）（P1）
- [ ] 添加 JS 变量赋值字符串扫描（Shopify.shopJsCdnBaseUrl）（P2）

#### LinkLocalizer 缺失功能（替换问题）
- [ ] 添加 `data-srcset` 属性支持（P0）
- [ ] 添加 ES module `import()` 字符串替换（P0）
- [ ] 添加 `meta[property="og:image"]` content 替换（P1）
- [ ] 添加 `<link rel="icon">` href 属性（P1）
- [ ] 添加 `<link rel="modulepreload">` href 属性（P1）
- [ ] JS 动态 `script.src` 赋值替换（P2）

#### 分析记录
- 问题已记录：`CHANGELOG.md` - `[2026-04-04] LinkLocalizer 未能处理的 URL 类型`
- 遗漏分析：25 个 URL PageParser 未提取

---

### 🎨 CSS 优化（未来计划）

> 龙老板想法：试试彻底解耦重写，但先不执行，完成 URL 本地化后再说

#### 方案 A：抽离 CSS 变量到 `:root {}`
- **投入**：中
- **收益**：HTML 更干净，减少冗余
- **做法**：从内联 `style=""` 中提取 `--variable: value` 到独立 CSS 文件的 `:root {}` 块

#### 方案 B：合并 `<style>` 到外部 CSS
- **投入**：中高
- **收益**：减少 HTML 大小，CSS 可缓存
- **做法**：同类型页面的 style 块合并为 1-2 个 link 引用

#### 方案 C：彻底解耦重写（长期）
- **投入**：极高
- **收益**：完整重构，架构清晰
- **做法**：使用 Shopify Theme Kit / Headless 方案重建
- **状态**：⚠️ 龙老板想试试，但先不执行

#### 推荐顺序
1. 先完成 URL 本地化（当前重点）
2. 后续做 CSS 变量抽离（方案 A）
3. 可选做 style 合并（方案 B）
4. 长期考虑方案 C（彻底重写）

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
