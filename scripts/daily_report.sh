#!/bin/bash
# 每日赛道追踪报告生成脚本
# crontab 配置：30 8 * * 1-5 /Users/jet/gangtise/scripts/daily_report.sh

set -e

TODAY=$(date "+%Y%m%d")
LOG_DIR="/Users/jet/gangtise/logs"
REPORT_DIR="/Users/jet/gangtise/docs/daily"

mkdir -p "$LOG_DIR" "$REPORT_DIR"

LOG_FILE="$LOG_DIR/daily_${TODAY}.log"

echo "[$(date)] 开始生成每日报告" >> "$LOG_FILE"

# 调用 claude CLI 触发 gangtise_daily_report 工具
claude --print \
  --allowedTools "gangtise_daily_report,gangtise_knowledge_search,gangtise_deep_research" \
  "使用 gangtise_daily_report 工具，生成今日赛道追踪报告。
赛道列表：半导体设备、半导体材料、先进封装、光通信。
要求：每个赛道包含最新券商观点、行业动态、投资机会与风险分析。
请将完整报告内容输出。" \
  >> "$REPORT_DIR/${TODAY}_daily_report.md" 2>> "$LOG_FILE"

echo "[$(date)] 报告生成完成：$REPORT_DIR/${TODAY}_daily_report.md" >> "$LOG_FILE"
