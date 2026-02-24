#!/usr/bin/env python3
"""
保存报告脚本
"""

import sys
import os

# 添加当前目录到 path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from technical_indicators import generate_technical_report

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python save_report.py <股票代码> <股票名称> [天数]")
        sys.exit(1)

    code = sys.argv[1]
    name = sys.argv[2]
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 180

    report = generate_technical_report(code, name, days)

    # 保存到 reports 目录
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    reports_dir = os.path.join(SCRIPT_DIR, "../../reports")
    os.makedirs(reports_dir, exist_ok=True)

    filename = os.path.join(reports_dir, f"{name}技术分析_{today}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"报告已保存到: {filename}")
