'''
Competitor Finder Tool - Identifies Industry Peers

This tool finds competitors for a given company by:
1. Looking up the company's industry sector
2. Finding other companies in the same sector
3. Filtering by similar market cap (real competitors are similar size)
4. Returning the top matches

Why this approach?
- Industry codes (GICS sectors) are standardized
- Market cap similarity ensures they're actual competitors
  (a $1B company doesn't compete with a $1T company)
- Uses yfinance which has comprehensive market data

Example:
Input: "TSLA" (Tesla)
Output: ["F" (Ford), "GM" (General Motors), "RIVN" (Rivian)]

Real-world use:
- Comparative analysis (how does Tesla's revenue compare to Ford's?)
- Investment research (what are the alternatives?)
- Market research (who are the key players?)
'''

import os
from typing import Dict, Any, List
from datetime import datetime
import yfinance as yf

#main function
def find_competitors(ticker: str) -> Dict[str, Any]:
    """
    Finds main competitors for a given company.
    
    Algorithm:
    1. Get target company's info (sector, industry, market cap)
    2. Search for companies in the same sector
    3. Filter by market cap range (0.3x to 3x of target)
    4. Return top 5 competitors
    
    Args:
        ticker: Stock ticker symbol (e.g., "TSLA")
        
    Returns:
        ToolResult with:
        - data: List of competitors with name, ticker, market cap
        - source: "yfinance market data"
        - confidence: 0.8 (reliable but not SEC-level)
        
    Example:
        result = find_competitors("TSLA")
        # Returns: {
        #   "success": True,
        #   "data": {
        #     "target_company": "Tesla, Inc.",
        #     "sector": "Consumer Cyclical",
        #     "industry": "Auto Manufacturers",
        #     "competitors": [
        #       {"ticker": "F", "name": "Ford", "market_cap": 52000000000},
        #       {"ticker": "GM", "name": "GM", "market_cap": 58000000000}
        #     ]
        #   },
        #   "confidence": 0.8
        # }
    """
    try:
        #Step 1 - Get target company information
        target = yf.Ticker(ticker.upper())
        target_info = target.info
    
        #Validate we got data
        if not target_info or 'sector' not in target_info:
            return _create_error_result(
                ticker,
                "Could not retrieve company information. Check ticker symbol"
            )
        #Extract key info
        company_name = target_info.get('longName', ticker.upper())
        sector = target_info.get('sector', 'Unknown')
        industry = target_info.get('industry', 'Unknown')
        target_market_cap = target_info.get('marketCap', 0)

        #Step 2 - Find competitors using a known list approach
        # Note: yfinance doesn't have a direct "find competitors" API
        # We'll use a hybrid approach:
        # 1. Check if we have a predefined competitor list
        # 2. Fall back to sector-based search  

        competitors = _get_competitors_by_sector(
            ticker = ticker.upper(),
            sector=sector,
            industry=industry,
            target_market_cap=target_market_cap
        )

        #Step 3 - format the result
        data = {
            "target_company": company_name,
            "target_ticker": ticker.upper(),
            "sector": sector,
            "industry": industry,
            "target_market_cap": target_market_cap,
            "competitors": competitors[:5],  # Top 5 only
            "total_found": len(competitors)
        }

        return {
            "tool_name": "find_competitors",
            "parameters": {"ticker": ticker},
            "data": data,
            "source": "yfinance market data + industry classification",
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.8,  # High confidence (market data is reliable)
            "success": True,
            "error": None
        }
    except Exception as e:
        return _create_error_result(ticker, str(e))

#Helper functions
def _get_competitors_by_sector(
    ticker: str,
    sector: str,
    industry: str,
    target_market_cap: float
) -> List[Dict[str, Any]]:
    '''
    '''
    pass 
