import os
import json
import asyncio
from typing import Dict, Any, Optional
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock, ResultMessage

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AGENTS_DIR = os.path.join(PROJECT_DIR, ".claude", "agents")
SKILLS_DIR = os.path.join(PROJECT_DIR, ".claude", "skills")


def load_agent_prompt(agent_name: str) -> str:
    agent_file = os.path.join(AGENTS_DIR, f"{agent_name}.md")
    if os.path.exists(agent_file):
        with open(agent_file, "r", encoding="utf-8") as f:
            return f.read()
    return ""


SYSTEM_PROMPT = """你是 TradingAgents 金融分析团队的协调者。你的任务是协调多个专业分析师对股票进行全面分析。

工作流程：
1. 首先获取股票基本信息（代码、名称、当前价格等）
2. 并行调用4个分析师：基本面分析师、技术分析师、情绪分析师、新闻分析师
3. 将分析结果交给多头研究员和空头研究员进行辩论
4. 风险管理员进行风险评估
5. 汇总所有分析，生成最终投资建议

团队成员：
- Fundamentals Analyst (基本面分析)
- Technical Analyst (技术分析)
- Sentiment Analyst (情绪分析)
- News Analyst (新闻分析)
- Bullish Researcher (多头研究)
- Bearish Researcher (空头研究)
- Risk Manager (风险评估)

重要提示：
- 必须调用 Claude Code 来执行分析
- 使用 --agent 参数指定要使用的智能体
- 每个分析师的详细定义在 .claude/agents/ 目录中
- 分析Skills定义在 .claude/skills/ 目录中
- 所有分析必须客观公正
- 最终报告必须包含风险提示：投资有风险，入市需谨慎
"""


async def call_agent(agent_name: str, prompt: str, cwd: str = PROJECT_DIR) -> str:
    agent_prompt = load_agent_prompt(agent_name)
    full_prompt = f"{agent_prompt}\n\n{prompt}" if agent_prompt else prompt
    
    options = ClaudeAgentOptions(
        cwd=cwd,
        max_turns=10,
    )
    
    result_text = ""
    async for message in query(prompt=full_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result_text += block.text
        elif isinstance(message, ResultMessage):
            result_text += message.content if hasattr(message, 'content') else str(message)
    
    return result_text


async def analyze_stock_team(code: str, name: str = "") -> Dict[str, Any]:
    stock_info = f"请分析股票 {code} {'(' + name + ')' if name else ''}"
    
    fundamentals_prompt = f"""{stock_info}

请执行基本面分析，包括但不限于：
1. 市盈率（PE）
2. 市净率（PB）
3. 净利润增长率
4. 资产负债率
5. 毛利率
6. 行业地位

请直接给出分析结论，无需过多解释。"""

    technical_prompt = f"""{stock_info}

请执行技术分析，包括但不限于：
1. 短期趋势（5日、10日）
2. 中期趋势（20日、60日）
3. 技术指标（MACD、KDJ、RSI）
4. 成交量分析
5. 支撑位和阻力位

请直接给出分析结论，无需过多解释。"""

    sentiment_prompt = f"""{stock_info}

请执行情绪分析，包括但不限于：
1. 市场情绪判断
2. 资金流向
3. 散户情绪
4. 机构持仓变化

请直接给出分析结论，无需过多解释。"""

    news_prompt = f"""{stock_info}

请搜索并分析相关新闻，包括但不限于：
1. 最新公告
2. 行业新闻
3. 宏观经济影响
4. 分析师评级

请直接给出分析结论，无需过多解释。"""

    results = {}
    
    try:
        results["fundamentals"] = await call_agent("fundamentals-analyst", fundamentals_prompt)
    except Exception as e:
        results["fundamentals"] = f"基本面分析失败: {str(e)}"
    
    try:
        results["technical"] = await call_agent("technical-analyst", technical_prompt)
    except Exception as e:
        results["technical"] = f"技术分析失败: {str(e)}"
    
    try:
        results["sentiment"] = await call_agent("sentiment-analyst", sentiment_prompt)
    except Exception as e:
        results["sentiment"] = f"情绪分析失败: {str(e)}"
    
    try:
        results["news"] = await call_agent("news-analyst", news_prompt)
    except Exception as e:
        results["news"] = f"新闻分析失败: {str(e)}"
    
    bull_bear_prompt = f"""基于以下分析结果，请进行多空辩论：

【基本面分析】
{results.get('fundamentals', '无')}

【技术分析】
{results.get('technical', '无')}

【情绪分析】
{results.get('sentiment', '无')}

【新闻分析】
{results.get('news', '无')}

请分别从多头和空头角度提出观点和论据。"""

    try:
        results["bullish"] = await call_agent("bullish-researcher", bull_bear_prompt)
    except Exception as e:
        results["bullish"] = f"多头研究失败: {str(e)}"
    
    try:
        results["bearish"] = await call_agent("bearish-researcher", bull_bear_prompt)
    except Exception as e:
        results["bearish"] = f"空头研究失败: {str(e)}"
    
    risk_prompt = f"""基于以下分析，请进行风险评估：

【多头观点】
{results.get('bullish', '无')}

【空头观点】
{results.get('bearish', '无')}

请评估投资风险，包括但不限于：
1. 市场风险
2. 行业风险
3. 公司风险
4. 流动性风险
5. 政策风险

请直接给出风险评估结论。"""

    try:
        results["risk"] = await call_agent("risk-manager", risk_prompt)
    except Exception as e:
        results["risk"] = f"风险评估失败: {str(e)}"
    
    summary_prompt = f"""基于以下完整分析，请生成最终投资建议：

【基本面分析】
{results.get('fundamentals', '无')}

【技术分析】
{results.get('technical', '无')}

【情绪分析】
{results.get('sentiment', '无')}

【新闻分析】
{results.get('news', '无')}

【多头观点】
{results.get('bullish', '无')}

【空头观点】
{results.get('bearish', '无')}

【风险评估】
{results.get('risk', '无')}

请生成最终投资建议，包括：
1. 投资评级（买入/持有/卖出）
2. 目标价位
3. 风险提示

重要提示：投资有风险，入市需谨慎。本分析仅供参考，不构成投资建议。"""

    try:
        results["summary"] = await call_agent("team-leader", summary_prompt)
    except Exception as e:
        results["summary"] = f"汇总失败: {str(e)}"
    
    results["code"] = code
    results["name"] = name
    
    return results
