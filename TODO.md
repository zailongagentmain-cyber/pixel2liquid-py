# Pixel2Liquid-Py TODO

**最后更新**: 2026-04-03

---

## Phase 1: 网页采集

### 已完成
- [x] `check_page_accessible()` - 检测页面可访问性 ✅ (2026-04-03)
- [x] `fetch_single_page()` - 获取单个页面 HTML ✅ (2026-04-03)

### 进行中
- [ ] `PageParser` - 页面结构解析，提取链接和资源 ✅ (2026-04-03)
- [ ] `CrawlState` - 爬取状态保存，断点续传

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
