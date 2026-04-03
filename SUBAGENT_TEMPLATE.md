# Subagent 任务模板

每次派 subagent 任务时，使用以下模板：

---

## 标准开头

```
# [模块名] 实现/修复任务

## 项目路径
`/Users/clawbot/projects/pixel2liquid-py/`
```

---

## 标准流程（必须执行）

### 1. 编码
- 按需求实现功能

### 2. 测试
- 写单元测试
- 运行测试确保通过

### 3. 提交代码
```bash
cd ~/projects/pixel2liquid-py
git add -A
git commit -m "[描述]"
git push
```

### 4. 汇报
- 测试结果
- 关键代码改动
- 示例输出

---

## 标准结尾

```
## 输出格式

完成后汇报：
1. 测试命令
2. 终端测试反馈（实际输出）
3. 关键代码改动
4. 示例/截图（如有）
```

---

## SOP 检查清单

- [ ] 编码完成
- [ ] 单元测试通过
- [ ] git commit + push
- [ ] 向主 session 汇报结果
