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
        filing = company.get_filings(form="10-Q").latest(1)
        if not filing:
            return _error_result(ticker, "No 10-Q filings found")
        
        xbrl = filing.xbrl()

        if not xbrl:
            return _error_result(ticker, "XBRL not available")
        
        #Extract metrics using GAAP tags from facts DataFrame
        financials = {}
        facts_df = xbrl.instance.facts
        
        #Revenue - search for revenue-related concepts
        revenue_tags = ["us-gaap:Revenues", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"]
        for tag in revenue_tags:
            try:
                rev_facts = facts_df[facts_df['concept'] == tag]
                if len(rev_facts) > 0:
                    # Find first numeric value (skip period strings like "P1Y")
                    for idx, row in rev_facts.iterrows():
                        try:
                            value = float(row['value'])
                            financials["revenue"] = {
                                "value": value,
                                "label": "Revenue",
                                "tag": tag
                            }
                            break
                        except (ValueError, TypeError):
                            continue
                    if "revenue" in financials:
                        break
            except (KeyError, TypeError, AttributeError, ValueError, IndexError):
                continue
        
        #Net income
        try:
            ni_facts = facts_df[facts_df['concept'] == "us-gaap:NetIncomeLoss"]
            if len(ni_facts) == 0:
                # Try case-insensitive search
                ni_facts = facts_df[facts_df['concept'].str.contains('NetIncome', case=False, na=False)]
            if len(ni_facts) > 0:
                value = ni_facts.iloc[0]['value']
                tag = ni_facts.iloc[0]['concept']
                if value is not None:
                    financials["net_income"] = {
                        "value": float(value),
                        "label": "Net Income",
                        "tag": tag
                    }
        except (KeyError, TypeError, AttributeError, ValueError, IndexError):
            pass
        if not financials:
            return _error_result(ticker, "Could not extract financials")
        
        #Build result
        filing_date = filing.filing_date.isoformat() if hasattr(filing.filing_date, 'isoformat') else str(filing.filing_date)
        report_date = filing.report_date.isoformat() if hasattr(filing, 'report_date') and hasattr(filing.report_date, 'isoformat') else (str(filing.report_date) if hasattr(filing, 'report_date') else None)
        
        data = {
            "ticker": ticker.upper(),
            "company_name": company.name,
            "filing_date": filing_date,
            "period_end": report_date,
            "financials": financials,
            "filing_url": filing.url if hasattr(filing, 'url') else str(filing)
        }

        return ToolResult(
            tool_name="sec_analyzer",
            parameters={"ticker": ticker},
            data=data,
            source=filing.url,
            timestamp=datetime.utcnow().isoformat(),
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

        