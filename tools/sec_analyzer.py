'''
SEC Analyzer - Extracts financials from 10-Q using XBRL (eXtensible Business Reporting Language.)
Why XBRL? It's structured, official, and error-free (no PDF parsing)
'''

import os
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Optional
from datetime import datetime
from edgar import Company, set_identity
from agent.state import ToolResult


def initialize_sec_access():
    #Set identity for SEC API
    user_agent = os.getenv("SEC_API_USER_AGENT", "Student student@example.com")
    set_identity(user_agent)

def get_latest_quarterly_financials(ticker: str) -> ToolResult:
    """
    Extract key financials from the latest 10-Q filing for a given ticker

    Returns ToolResult with:
    - data: {revenue, net_income, operating_expenses, etc}
    - source: SEC filing URL
    - confidence: 1.0 (XBRL is highest quality)
    """
    try:
        initialize_sec_access()
        #Get company
        company = Company(ticker.upper())
        #get latest 10-Q
        filing = filings[0]
        xbrl = filing.xbrl()

        if not xbrl:
            return _error_result(ticker, "XBRL not available")
        
        #Extract metrics using GAAP tags
        financials = {}

        #Revenue
        for tag in ["us-gaap:Revenues", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"]:
            try:
                value = xbrl[tag]
                if value:
                    financials["revuenue"] = {
                        "value": float(value),
                        "label": "Revenue",
                        "tag": tag
                    }
                    break
            except (KeyError, TypeError):
                continue
        
        #Net income
        try:
            value = xbrl["us-gaap:NetIncomeLoss"]
            if value:
                financials["net_income"] = {
                    "value": float(value),
                    "label": "Net Income",
                    "tag": "us-gaap:NetIncomeLoss"
                }
        except (KeyError, TypeError):
            pass
        if not financials:
            return _error_result(ticker, "Could not extract financials")
        
        #Build result
        data = {
            "ticker": ticker.upper(),
            "company_name": company.name,
            "filing_date": filing.filing_date.isoformat(),
            "period_end": filing.period_of_report.isoformat() if filing.period_of_report else None,
            "financials": financials,
            "filing_url": filing.url
        }

        return ToolResult(
            tool_name="sec_analyzer",
            parameters={"ticker": ticker},
            data=data,
            source=filing.url,
            timestamp=datetime.utc.now().isoformat(),
            confidence=1.0, #XBRL = highest confidence
            success=True,
            error=None
        )
    except Exception as e:
        return _error_result(ticker, str(e))
    
def _error_result(ticker: str, error_msg: str) -> ToolResult:
    #Helper for error results
    return ToolResult(
        tool_name="sec_analyzer",
        parameters={"ticker": ticker},
        data=None,
        source="SEC EDGAR",
        timestamp=datetime.utcnow().isoformat(),
        confidence=0.0,
        success=False,
        error=error_msg
    )

        