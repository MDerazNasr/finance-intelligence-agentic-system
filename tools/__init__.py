"""
Tools package - contains all agent tools

Available tools:
1. get_latest_quarterly_financials - SEC XBRL financial data (confidence: 1.0)
2. find_competitors - Industry peer discovery (confidence: 0.8)
3. get_top_companies - Market cap rankings (confidence: 0.8) [Phase 2]
4. research_ai_disruption - AI use case research (confidence: 0.7) [Phase 2]
5. general_financial_research - Fallback web research (confidence: 0.7) [Phase 2]
"""

import sys
from pathlib import Path

# Ensure project root is in path for absolute imports
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.sec_analyzer import get_latest_quarterly_financials
from tools.competitor_finder import find_competitors
from tools.generate_research import general_financial_research

__all__ = [
    "get_latest_quarterly_financials", 
    "general_financial_research",
    "find_competitors"
    ]
