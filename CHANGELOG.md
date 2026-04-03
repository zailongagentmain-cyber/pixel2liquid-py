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
- 成功: 51
- 失败: 9（其中 4 个是真实死链，1 个是认证拦截，4 个是别名/重复）
- 成功率: 91.7%

**结论**: 这是网站结构问题，不是代码 bug

---

*此文件在项目开发过程中持续更新*
