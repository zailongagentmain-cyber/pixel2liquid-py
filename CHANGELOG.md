# Changelog - 错误和修改记录

**目的**：记录犯过的错，避免重复犯错

---

## [YYYY-MM-DD] <模块>.<函数名>

**问题**: 

**原因**: 

**修改**: 

**验证**: 

---

## 示例

### [2026-04-03] spider.fetch_page

**问题**: 状态码 404 但函数返回成功

**原因**: 没有检查 HTTP 状态码，只检查了响应体非空

**修改**: 添加状态码检查，4xx 返回 False

**验证**: `pytest tests/test_spider.py::test_spider__fetch_page__404 -v`

---

## [2026-04-03] fandomara.com 全量爬取发现死链

**问题**: 爬取 fandomara.com 时发现 9 个 URL 失败，其中部分是网站本身的死链

**原因分析**:
- 网站主页 HTML 包含指向不存在页面的链接（单复数问题、别名问题）
- `/collections/ita-bag`（单数）→ 网站只有 `/collections/ita-bags`（复数）
- `/collections/plushie` → 网站正确名称是 `/collections/love-and-deepspace-plushies`
- `/collections/shop-all` → 网站不存在此页面
- `/customer_authentication/redirect` → 正常拦截（需要认证）

**代码行为**:
- ✅ 代码正确提取了所有链接（包括死链）
- ✅ 尝试爬取后收到 404
- ✅ 正确标记为失败并继续爬取其他页面

**统计**:
- 总页面: 60

---

## [2026-04-04] LinkLocalizer 未能处理的 URL 类型

**问题描述**: localized/www.fandomara.com.html 中有 82 个 cdn.shopify.com URL 未被替换

**分析统计**:
- total_found: 82
- inline_script: 48（JS 动态创建 script.src 赋值）
- data_attribute: 21（data-srcset 等）
- src_href: 9（普通 img src）
- content_meta: 2（og:image meta）
- link_href: 1（favicon）
- import: 1（ES module dynamic import）

**在 manifest 中但未替换的（40个）**:
- data-srcset 属性（21个）：LinkLocalizer 未处理 data-srcset
- import() 动态导入（1个）：JS 字符串无法被 attribute 替换
- inline script 变量赋值（Shopify.shopJsCdnBaseUrl 等）：JS 变量赋值
- modulepreload link（1个）：未处理 <link rel="modulepreload">

**不在 manifest 中的（42个）**:
- 原因待排查（见任务2）
- 可能：PageParser 遗漏、下载失败、URL 规范化问题

**LinkLocalizer 缺失功能**:
1. data-srcset 属性支持（P0）
2. ES module import() 字符串替换（P0）
3. meta og:image content 属性（P1）
4. link rel="icon" href 属性（P1）
5. link rel="modulepreload" href 属性（P1）
6. JS 动态 script.src 赋值（P2）

**建议修复方向**:
- P0: 添加 data-srcset 支持 + import() 支持
- P1: 添加更多 HTML 属性支持
- P2: 需要 JS 运行时替换或预处理器

**修复验证命令**: 待修复后运行 LinkLocalizer 重跑 localized
- 成功: 51
- 失败: 9（其中 4 个是真实死链，1 个是认证拦截，4 个是别名/重复）
- 成功率: 91.7%

**结论**: 这是网站结构问题，不是代码 bug

---

---

## [2026-04-04] 分层复刻方案确认

**背景**: 原站使用 Shopify + PageFly/GemCommerce，目标迁移到目标 Shopify

**方案**: 分层处理
- Layer 1 静态视觉（CSS/动画/布局）→ 提取并重写 ✅
- Layer 2 页面结构（HTML → Liquid）→ 可以做 ✅
- Layer 3 动态内容（Shopify 对象）→ 原生支持 ✅
- Layer 4 JS 交互 → 部分可以做，App 功能无法复刻 ⚠️

**结论**: 视觉 100% 可复刻，App 功能需用 Shopify 原生方案重建

**文档**: `LAYERED_MIGRATION.md`

---

*此文件在项目开发过程中持续更新*
