# Pixel2Liquid-Py TODO

**最后更新**: 2026-04-03

---

## 项目初始化

## 项目初始化

- [x] 确定技术栈细节（httpx vs aiohttp）
- [x] 初始化 Python 项目（uv）
- [ ] 配置 black/ruff/mypy
- [x] 建立目录结构

---

## Phase 1: 网页采集

- [ ] 基础页面采集（单页面）
  - [x] `check_page_accessible()` - 检测页面可访问性 ✅
  - [ ] `fetch_single_page()` - 获取单个页面 HTML
  - [ ] `extract_links()` - 提取页面链接
  - [ ] `extract_assets()` - 提取资源链接
- [ ] 资源链接提取（CSS/JS/Images/Fonts）
- [ ] 站内链接追踪
- [ ] 断点续传
- [ ] 进度显示
- [ ] 单元测试

**验证标准**: 成功率 >95%

---

## Phase 2: 格式转换

- [ ] HTML 解析
- [ ] HTML → Liquid 转换
- [ ] 路径修复
- [ ] CDN URL 替换
- [ ] 单元测试

**验证标准**: 转换完整度 >90%

---

## Phase 3: CDN 处理

- [ ] 资源去重
- [ ] URL 映射表
- [ ] Protocol-relative URL 修复
- [ ] 单元测试

**验证标准**: URL 替换正确率 >95%

---

## Phase 4: Shopify 适配

- [ ] Shopify 主题结构生成
- [ ] 资源上传
- [ ] Shopify CLI 集成
- [ ] 单元测试

**验证标准**: 可成功导入 Shopify

---

## Phase 5: CLI 工具化

- [ ] Click/Typer CLI 框架
- [ ] 命令实现
- [ ] 帮助文档
- [ ] 配置文件支持

**验证标准**: 工具可独立使用

---

## 已完成

| 日期 | 完成项 |
|------|--------|
| 2026-04-03 | 创建 SPEC.md |
| 2026-04-03 | 创建 SOP.md |
| 2026-04-03 | 创建 TODO.md |
