# 分层复刻方案

**创建日期**：2026-04-04
**状态**：已确认

---

## 背景

原站使用 Shopify + PageFly/GemCommerce 构建。
目标是提取原站资源，重建到目标 Shopify 店铺。

---

## 分层架构

### Layer 1：静态视觉（我们能做 ✅）

| 资源类型 | 处理方式 |
|----------|---------|
| 静态 CSS 规则 | 提取到独立 CSS 文件 |
| 内联样式 | 合并到 CSS 文件 |
| CSS 变量 | 提取到 `:root {}` |
| 布局配置 | CSS grid/flexbox |
| CSS 动画 | `@keyframes` + `transition` |
| 响应式 | Media queries |

**能做到 100% 视觉复刻。**

### Layer 2：页面结构（我们能做 ✅）

| 资源类型 | 处理方式 |
|----------|---------|
| HTML DOM 层级 | 映射到 Liquid 模板结构 |
| 文字内容 | 提取并迁移 |
| 图片资源 | 下载 → 上传 Shopify assets |

**能做到 100% 结构复刻。**

### Layer 3：动态内容（Shopify 原生 ✅）

| 资源类型 | 处理方式 |
|----------|---------|
| 产品数据 | Shopify Admin API 迁移（已完成）|
| Collections | Shopify Admin API 迁移（已完成）|
| Shopify 对象 | Liquid 模板语言实现 |

**能做到 100% 功能复刻。**

### Layer 4：JS 交互（需要额外工作 ⚠️）

| 资源类型 | 处理方式 |
|----------|---------|
| AJAX Add to Cart | Shopify AJAX API 或自定义 JS |
| 滚动动画 | 添加到 theme.js |
| 第三方追踪器 | 下载并迁移（如 Parkour Pixel）|
| PageFly 编辑器 | ❌ 放弃（App 特有功能）|
| GemCommerce 组件 | ❌ 放弃（App 特有功能）|

---

## 关键限制

### 无法完美复制的

| 功能 | 原因 | 替代方案 |
|------|------|---------|
| App 拖拽编辑 | PageFly 等是 App 功能，不是页面内容 | 在目标站用 Shopify 原生 Sections 重建 |
| JS 动态 DOM | 无法从静态 HTML 提取 | 用 Liquid 重写该区块 |
| 运行时状态 | JS 设置的 sessionStorage 等 | Shopify 状态管理有限 |

### 可以复制的

| 功能 | 说明 |
|------|------|
| 视觉外观 | CSS 100% 可提取并重写 |
| 页面结构 | HTML → Liquid 模板 |
| 动画效果 | CSS @keyframes |
| 布局 | CSS grid/flexbox |
| 颜色/字体 | CSS 变量 |

---

## 执行流程

### Phase 1：资源提取
1. PageParser 提取所有资源 URL
2. AssetDownloader 下载资源
3. ManifestManager 维护映射表

### Phase 2：资源分类
1. 分类：Shopify CDN / App 资源 / 外部 CDN
2. Shopify CDN → 下载并上传到目标 Shopify
3. App 资源 → 判断是否需要迁移
4. 外部 CDN → 保留引用或下载

### Phase 3：代码生成
1. 提取 CSS 到独立文件
2. 生成 Liquid 模板结构
3. 提取设计 Token（颜色、字体等）

### Phase 4：Shopify 部署
1. 上传 assets 到 Shopify
2. 部署 Liquid 模板
3. 验证页面外观

---

## 工具支持

| 工具 | 用途 |
|------|------|
| pixel2liquid-py | 资源下载 + URL 替换 |
| Shopify CLI | 上传 assets + 部署主题 |
| Browser DevTools | 分析页面结构 |
| AI 辅助 | 生成 Liquid 代码 |

---

## 状态

- [x] 分层方案已确认（2026-04-04）
- [ ] PageParser P0 修复（data-srcset, og:image, etc.）
- [ ] LinkLocalizer P0 修复（data-srcset, import(), etc.）
- [ ] CSS 提取到独立文件
- [ ] Liquid 模板生成
- [ ] Shopify 部署

---

## GemPage / GemCommerce 迁移分析（2026-04-04）

### 关键发现

GemPage 的 CSS 类名（如 `gp-*`, `gprow`, `gpcol`）和懒加载 JS 是**强绑定的**：

1. `gp-*` CSS 类依赖 `gp-lazyload.v2.js` 才能正确工作
2. `gp-lazyload.v2.js` 依赖 Shopify CDN URL 格式处理响应式图片
3. 这些类名是 GemPage App 特有的，不是标准 CSS

### 组件分类

| 组件 | 能否迁移 | 说明 |
|------|---------|------|
| HTML DOM 结构 | ✅ 可以分析 | 作为设计参考 |
| `gp-*` CSS 类名 | ❌ 不行 | 依赖 GemPage JS |
| 布局逻辑 (Grid/Flex) | ⚠️ 部分可以 | 需重写选择器 |
| `gp-lazyload.v2.js` | ❌ 不行 | App 特有 JS |
| 响应式图片处理 | ⚠️ 可以 | 用 Shopify image_url filter |
| Shopify 图片 URL 格式 | ✅ 可以 | 下载后重新生成 |

### 迁移方案

**不要尝试复制 `gp-*` 类到目标 Shopify**

正确的做法：
1. 分析原站 HTML 结构 → 作为设计参考
2. 用 Shopify 原生 Sections/Blocks 重建区块
3. 使用 Shopify 的 CSS Grid/Flexbox 实现类似布局
4. 用 `{{ product.featured_image | image_url: width: 768 }}` 处理响应式图片
5. Shopify 原生 `loading="lazy"` 替代 GemPage 懒加载

### 示例对比

**原站 (GemPage)**：
```html
<div class="gp-grid gp-w-full">
  <div class="gprow">
    <div class="gpcol gp-flex">
      <img class="gps-lazy" data-src="...">
    </div>
  </div>
</div>
```

**迁移后 (Shopify 原生)**：
```liquid
{% schema %}
{
  "name": "Custom Grid",
  "blocks": [
    { "type": "image" }
  ]
}
{% endschema %}

<div class="custom-grid">
  {% for block in section.blocks %}
    <div class="grid-item">
      {{ block.settings.image | image_url: width: 768 | image_tag: loading: "lazy" }}
    </div>
  {% endfor %}
</div>
```

### 结论

> ⚠️ App 特有的 CSS/JS 无法直接迁移，需要用 Shopify 原生方案重建
>
> 参考原站的设计和布局，用目标平台的原生方式实现

### 待讨论

- [ ] 如何提取"设计规格"而非直接复制代码
- [ ] Shopify 区块的响应式布局最佳实践
- [ ] 图片处理：CDN URL → Shopify image_url filter
