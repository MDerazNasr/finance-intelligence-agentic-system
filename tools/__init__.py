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

# Lazy imports to avoid circular import issues
# Import only when explicitly accessed, not at module load time
def _lazy_import_sec_analyzer():
    from tools.sec_analyzer import get_latest_quarterly_financials
    return get_latest_quarterly_financials

def _lazy_import_competitor_finder():
    from tools.competitor_finder import find_competitors
    return find_competitors

def _lazy_import_generate_research():
    from tools.generate_research import general_financial_research
    return general_financial_research

# Use __getattr__ for lazy loading (Python 3.7+)
def __getattr__(name: str):
    if name == "get_latest_quarterly_financials":
        return _lazy_import_sec_analyzer()
    elif name == "find_competitors":
        return _lazy_import_competitor_finder()
    elif name == "general_financial_research":
        return _lazy_import_generate_research()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "get_latest_quarterly_financials", 
    "general_financial_research",
    "find_competitors"
    ]
