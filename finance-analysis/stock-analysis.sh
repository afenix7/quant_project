#!/bin/bash

# 金融分析团队启动脚本
# 用法: ./stock-analysis.sh <股票代码> [股票名称]
# 示例: ./stock-analysis.sh 603893 瑞芯微

set -e

if [ -z "$1" ]; then
    echo "用法: $0 <股票代码> [股票名称]"
    echo "示例: $0 603893 瑞芯微"
    exit 1
fi

STOCK_CODE=$1
STOCK_NAME=${2:-""}

echo "============================================"
echo "  TradingAgents 金融分析团队"
echo "============================================"
echo "目标股票: $STOCK_CODE $STOCK_NAME"
echo "分析时间: $(date '+%Y年%m月%d日')"
echo "============================================"
echo ""

# 检查是否有 opencode 命令
if ! command -v opencode &> /dev/null; then
    echo "错误: 未找到 opencode 命令"
    exit 1
fi

# 启动分析
echo "正在启动金融分析团队..."
echo ""

# 这里的命令会启动 team-leader 进行分析
# 由于需要交互式使用，直接提示用户下一步操作
cat << 'EOF'

分析流程已准备就绪！

请在 opencode 中执行以下操作来启动完整分析：

1. 加载 team-leader 技能:
   /use team-leader

2. 或者直接发送分析请求:
   "分析股票 $STOCK_CODE $STOCK_NAME"

3. 团队将自动执行以下分析流程:
   - 基本面分析
   - 技术分析
   - 情绪分析
   - 新闻分析
   - 多头研究
   - 空头研究
   - 风险评估
   - 最终报告汇总

EOF

echo "分析脚本创建完成！"
echo ""
echo "下一步: 在 opencode 中使用此脚本进行股票分析"
