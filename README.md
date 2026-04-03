# Pixel2Liquid-Py

网站核心资源采集工具 - Python 版本

## 核心目标

准确获取网站的核心资源（HTML/CSS/JS/Images/Fonts）

## 文档

- [SPEC.md](./SPEC.md) - 项目规格（Phase 定义）
- [SOP.md](./SOP.md) - 工作方式规范
- [TODO.md](./TODO.md) - 待办列表

## 当前 Phase

**Phase 1: 网页采集** — 准备开始

## 技术栈

- Python 3.11+
- uv（包管理）
- httpx / aiohttp（HTTP 客户端）
- BeautifulSoup / lxml（HTML 解析）
- Click / Typer（CLI）

## 快速开始

```bash
# 克隆项目
cd pixel2liquid-py

# 安装依赖
uv sync

# 运行测试
pytest tests/ -v
```

---

*项目初始化: 2026-04-03*
