# 股票分析 Trading Agent 任务计划

## 目标
在现有 quant_project 中增加股票分析功能，允许用户在前端页面启动 trading agent 进行股票分析。

## 现有代码
- 后端: `/root/quant_project/backend/main.py`
- 前端: `/root/quant_project/frontend/src/App.js`
- 分析脚本: `/root/quant_project/finance-analysis/stock_analysis.py`

## 阶段

### Phase 1: 后端 API
- [ ] 添加股票分析 API 接口 `/api/analyze`
- [ ] 集成 stock_analysis.py 的分析逻辑
- [ ] 返回结构化分析结果

### Phase 2: 前端组件
- [ ] 添加股票分析输入组件
- [ ] 添加分析结果展示组件
- [ ] 添加加载状态和错误处理

### Phase 3: 集成
- [ ] 页面布局调整
- [ ] API 调用集成
- [ ] 测试验证

## 依赖
- Python: requests (stock_analysis.py 已使用)
- 前端: 现有依赖已满足

## 进度
- [x] 复制 finance-analysis 代码到 quant_project
- [x] 创建任务计划
- [ ] 实现后端 API
- [ ] 实现前端组件
