# Pixel2Liquid-Py - 工作方式 SOP

**目的**：确保每次工作方式一致，避免重复错误

**适用范围**：pixel2liquid-py 项目所有开发工作

---

## 核心原则

### 1. 验证驱动开发
```
代码修改 → 立即测试 → 验证结果 → 提交git
```
❌ 不验证就结束
✅ 每一步都必须有验证结果

### 2. 任务分工
| 任务类型 | 执行者 | 说明 |
|----------|--------|------|
| 代码实现 | subagent | 可验证、可回滚 |
| 调研分析 | 主 session | 需要上下文 |
| 部署/CLI | subagent | 需要独立环境 |
| 重大决策 | 龙老板 | 需要确认 |

### 3. 进度汇报
- 每完成一个子任务 → 立即汇报
- 遇到问题 → 立即停止并汇报
- 不攒到最后一起汇报

### 4. 中间结果必须保存
- **每个小的功能块**对应的输出，如果对下一步实验有意义，就应该保存
- 保存的目的是：后续开发/测试不需要重复执行前面的功能
- 保存粒度：**细粒度**，不只是 Phase 级别
- 保存时机：功能块验证通过后立即保存
- 文件命名：`<功能>_cache.json` 或放在 `cache/` 目录
- 禁止：只保存在内存中，session 结束后丢失

**示例**：
```bash
# PageParser 验证通过后，保存解析结果
cache/fandomara_pages.json

# SiteCrawler 爬取完成后，保存完整状态
cache/crawl_state.json

# 资源下载后，保存 URL → 本地路径映射
cache/assets_manifest.json
```

---

## 小模块开发流程（核心）

### 技术栈讨论
在实现每个功能前，必须讨论：
1. **技术栈选择**：用什么库/工具？
2. **实现方式**：直接用还是自己封装？
3. **依赖原则**：**能使用现成的 Python 库，就不要自行进行代码工作**

### Phase X 开发 checklist

### 原则
- **每个函数/类方法 = 独立模块**
- **先写测试，再写实现**
- **每步验证，立即反馈**

### 开发 checklist

1. **理解需求** — 这个函数要做什么
2. **讨论技术栈** — 用什么库？优先现成库
3. **记入 DESIGN.md** — 功能目的、技术栈、测试方式、预期结论
4. **写测试函数** — 明确「完成」的标准
5. **实现函数** — 最小代码
6. **运行测试** — 命令行调用
7. **验证结果** — 符合预期？
8. **如果有问题** — 记录 changelog，修复，重复 6-8
9. **提交** — git commit

---

## 测试流程

### 测试命令模板

```bash
# 格式
pytest tests/<模块名>.py::<测试函数> -v

# 示例
pytest tests/test_spider.py::test_spider__fetch_single_page__success -v
```

### 测试前汇报

**测试前，我必须告诉你**：
- **命令**: `pytest tests/test_spider.py::test_spider__fetch_single_page__success -v`
- **目的**: 验证 `fetch_single_page()` 成功获取 HTML
- **预期**: 返回状态码 200，HTML 长度 > 1000

### 测试后汇报

**测试后，我必须呈现**：
- **实际结果**: 终端输出内容
- **是否符合预期**: 是/否
- **如果有问题**: 错误原因 + 修改计划

---

## Changelog（错误记录）

### 触发条件
- 测试失败
- 行为与预期不符
- 需要修改已完成的代码

### 格式

```markdown
## Changelog

### [YYYY-MM-DD] <模块名>.<函数名>

**问题**: <描述>

**原因**: <为什么会犯错>

**修改**: <怎么改正>

**验证**: <用什么命令/方式验证>
```

### 示例

```markdown
## Changelog

### [2026-04-03] spider.fetch_page

**问题**: 状态码 404 但函数返回成功

**原因**: 没有检查 HTTP 状态码，只检查了响应体非空

**修改**: 添加状态码检查，4xx 返回 False

**验证**: `pytest tests/test_spider.py::test_spider__fetch_page__404 -v`
```

---

## 代码修改记录

### 触发条件
- 任何代码修改（不只是错误修复）

### 格式

```markdown
## 代码修改记录

### [YYYY-MM-DD] <简短描述>

**文件**: <path/to/file.py>
**函数**: <function_name>

**修改前**: <简单描述>
**修改后**: <简单描述>

**原因**: <为什么修改>
```

---

## 验证节点

每个 Phase 完成后，必须验证：

| Phase | 验证项 |
|-------|--------|
| Phase 1 | 能否成功采集 3 个以上页面？资源是否完整？ |
| Phase 2 | HTML → Liquid 转换是否正确？ |
| Phase 3 | URL 替换是否完整？ |
| Phase 4 | 能否成功推送到 Shopify？ |
| Phase 5 | CLI --help 是否可用？ |

---

## 目录结构约定

```
pixel2liquid-py/
├── SPEC.md              # 项目规格（Phase 定义）
├── SOP.md               # 本文件（工作方式）
├── TODO.md              # 当前待办
├── src/
│   └── pixel2liquid/
│       ├── spider.py        # Phase 1
│       ├── transformer.py   # Phase 2
│       ├── cdn_handler.py   # Phase 3
│       └── shopify.py       # Phase 4
└── tests/
    ├── test_spider.py       # Phase 1 测试
    ├── test_transformer.py  # Phase 2 测试
    ├── test_cdn_handler.py  # Phase 3 测试
    └── test_shopify.py      # Phase 4 测试
```

---

## 测试要求

### 每个 Phase 必须有测试
| Phase | 最低测试覆盖 |
|-------|-------------|
| Phase 1 | `test_spider.py` |
| Phase 2 | `test_transformer.py` |
| Phase 3 | `test_cdn_handler.py` |
| Phase 4 | `test_shopify.py` |

### 测试命名规范
```python
def test_xxx__expected_behavior__when_condition():
    """格式: test_<功能>__<预期结果>__<条件>"""
```

### 运行测试
```bash
# 单个测试
pytest tests/test_spider.py -v

# 所有测试
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=src/pixel2liquid --cov-report=term-missing
```

---

## Git 提交规范

### 提交信息格式
```
[<Phase>] <简短描述>

<详细说明（可选）>

Closes: #<issue号>
```

### 示例
```
[Phase 1] 添加基础页面采集功能

- 支持单页面 HTML 采集
- 支持资源链接提取
- 添加断点续传

Closes: #1
```

### 提交时机
- 每个 Phase 完成后提交一次
- 或者每个独立功能完成后提交
- ❌ 不要积累大量修改后一次性提交

---

## 代码风格

| 规则 | 工具 |
|------|------|
| 格式化 | black |
| Lint | ruff |
| 类型检查 | mypy |

### 运行
```bash
# 格式化
black src/ tests/

# Lint
ruff check src/ tests/

# 类型检查
mypy src/
```

---

## 错误处理

### 遇到错误的正确姿势
1. 停止当前操作
2. 记录错误信息
3. 分析原因
4. 汇报给龙老板（如果是阻塞性问题）
5. 继续（如果是小问题）

### 错误日志格式
```
[<时间戳>] ERROR | <模块> | <错误描述>
  原因: <分析>
  尝试: <已尝试的解决方案>
```

---

## 会话管理

### 开始新工作前
1. 检查 SESSION-FLUSH.md 是否有未完成的工作
2. 检查 TODO.md 确认优先级
3. 检查是否有未提交的修改

### 结束工作时
1. 更新 SESSION-FLUSH.md
2. 更新 TODO.md（标记完成项）
3. 汇报给龙老板

---

## 配置文件

### 项目级配置
```yaml
# .pixel2liquid.yaml
project:
  name: pixel2liquid-py
  version: 0.1.0

shopify:
  store_url: https://claw-test-2.myshopify.com
  # token 从环境变量或 secrets 获取
```

### secrets 管理
- Token 不存储在代码或配置文件中
- 使用环境变量或 `~/.openclaw/secrets/`

---

## 验证节点

每个 Phase 完成后，必须验证：

| Phase | 验证项 |
|-------|--------|
| Phase 1 | 能否成功采集 3 个以上页面？资源是否完整？ |
| Phase 2 | HTML → Liquid 转换是否正确？ |
| Phase 3 | URL 替换是否完整？ |
| Phase 4 | 能否成功推送到 Shopify？ |
| Phase 5 | CLI --help 是否可用？ |

---

## 常见问题处理

### Q: subagent 超时怎么办？
A: 拆分任务为更小的单元，确保每个 subagent 任务在 5 分钟内完成

### Q: 测试失败怎么办？
A: ❌ 不要跳过或忽略测试
✅ 修复代码使测试通过

### Q: 需要做决策但龙老板不在线？
A: ❌ 不要自己决定重大事项
✅ 记录问题，等龙老板确认

---

## SOP 维护

| 更新时间 | 更新内容 |
|----------|----------|
| 2026-04-03 | 初始版本 |

---

*本文档规定了 pixel2liquid-py 项目的工作方式，违反即为错误*
