# Task Plan: AI 团队股票分析报告功能开发

## Goal
在前端 AI 团队分析 tab 中添加股票代码/名称输入框和分析按钮，并在分析完成后用 react-markdown 渲染 markdown 格式的报告内容。

## Current Phase
Phase 1

## Phases

### Phase 1: 前端界面完善
- [ ] 检查前端 AI 团队分析 tab 是否已有输入框组件
- [ ] 确认 API 调用逻辑
- [ ] 安装 react-markdown 依赖
- [ ] **Status:** in_progress

### Phase 2: 后端 markdown 内容优化
- [ ] 修改 agent_service.py 让各分析师返回 markdown 格式内容
- [ ] 更新提示词引导 markdown 输出
- [ ] **Status:** pending

### Phase 3: 前端渲染 markdown
- [ ] 导入 react-markdown
- [ ] 修改报告展示组件，用 react-markdown 渲染各字段
- [ ] 添加必要的 CSS 样式
- [ ] **Status:** pending

### Phase 4: 测试验证
- [ ] 启动前后端服务
- [ ] 测试 AI 团队分析功能
- [ ] 验证 markdown 渲染效果
- [ ] **Status:** pending

## Key Questions
1. 前端 AI 团队分析 tab 现有代码是否完整？（代码 line 667-791 显示已有输入框和结果展示）
2. 后端返回的各字段内容是否需要改为 markdown 格式？

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 使用 react-markdown 渲染 | 用户推荐，业界标准方案 |
| 保持字段结构不变 | 方案 A，结构清晰，改动最小 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| - | - | - |

## Notes
- 方案 A: 保持字段结构（fundamentals、technical 等），各字段内容改为 markdown
- 前端已有 AI 团队分析 tab (line 667-791)，但需要确认是否正常工作
- 后端 agent_service.py 需要调整各分析师的提示词，输出 markdown 格式
