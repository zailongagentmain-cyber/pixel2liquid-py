# 彻底解耦重写想法

**创建日期**：2026-04-04
**创建人**：龙老板
**状态**：⚠️ 先记录，暂不执行

---

## 背景

Shopify 主题的 CSS 与 HTML 高耦合：
- 67 个 `<style>` 标签（产品页）
- 350,477 条 CSS 规则
- 777 个内联 `style=""` 属性
- Shopify 缩写属性（`--bc`, `--bs`, `--bw`, `--pageType:GP_PRODUCT`）

---

## 方案思路

### 方向 1：Shopify Theme Kit + GitHub 集成
- 使用 Shopify 官方 Theme Kit
- 主题代码克隆到 GitHub
- 独立开发、测试、部署
- **优点**：官方支持，完整主题结构
- **缺点**：需要 Shopify 账户权限，主题本身有依赖

### 方向 2：Headless 方案（Storefront API）
- 前端完全独立（Next.js/Gatsby）
- 后端 Shopify 只做数据
- **优点**：最灵活，前端完全可控
- **缺点**：重做整个 storefront，工作量大

### 方向 3：部分解耦
- 保留 Shopify 主题结构
- 只抽离 CSS 到独立文件
- 使用 Shopify 的 CSS 管道
- **优点**：改动较小
- **缺点**：无法完全解耦

---

## 龙老板的想法

> "我还是回头想试试，但现在先不着急执行"

- 先完成 URL 本地化
- 后续评估 CSS 优化效果
- 再决定是否需要彻底重写

---

## 什么时候考虑这个方案？

- URL 本地化完成后，CSS 冗余问题仍然严重
- 需要二次开发主题功能
- 需要更好的开发体验（热更新、组件化）

---

## 参考资料

- [Shopify Theme Kit](https://shopify.dev/docs/themes/tools/theme-kit)
- [Shopify Storefront API](https://shopify.dev/docs/api/storefront)
- [Shopify GitHub Integration](https://shopify.dev/docs/themes/tools/github)
