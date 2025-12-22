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
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf

# Cache configuration
CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_DURATION_HOURS = 24  # Cache data for 24 hours

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
        #Step 1 - Get target company information (with caching)
        target_info = _get_cached_ticker_info(ticker.upper())
    
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
    Finds competitors using sector + market cap filtering.
    
    Strategy:
    1. Use a predefined list of major tickers by sector
    2. Filter to the same sector
    3. Filter by similar market cap (0.3x to 3x)
    4. Exclude the target company itself
    
    Why this approach?
    - yfinance doesn't have a "search by sector" API
    - We maintain a curated list of major companies
    - This is fast and doesn't require web scraping
    - Good enough for demo purposes
    
    Args:
        ticker: Target company ticker
        sector: Target company's sector
        industry: Target company's industry
        target_market_cap: Target company's market cap
        
    Returns:
        List of competitor dicts with ticker, name, market_cap
    '''
    #Predefined list of major public companies by sector
    #In production, this would be a database or API call
    MAJOR_TICKERS_BY_SECTOR = {
        "Technology": [
            "AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AVGO", "ORCL",
            "ADBE", "CRM", "CSCO", "ACN", "AMD", "INTC", "IBM", "QCOM", "TXN"
        ],
        "Consumer Cyclical": [
            "AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "TM", "F", "GM",
            "BKNG", "LOW", "TGT", "ABNB", "MAR", "RIVN", "LCID"
        ],
        "Healthcare": [
            "UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "PFE", "DHR",
            "BMY", "AMGN", "CVS", "CI", "ELV", "HCA", "ISRG"
        ],
        "Financial Services": [
            "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "SPGI",
            "BLK", "C", "AXP", "CB", "PGR", "MMC", "SCHW"
        ],
        "Communication Services": [
            "META", "GOOGL", "GOOG", "NFLX", "DIS", "CMCSA", "TMUS", "VZ", "T"
        ],
        "Consumer Defensive": [
            "WMT", "PG", "COST", "KO", "PEP", "PM", "MO", "EL", "CL", "KMB"
        ],
        "Energy": [
            "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY"
        ],
        "Industrials": [
            "UPS", "RTX", "HON", "UNP", "BA", "CAT", "GE", "LMT", "DE", "MMM"
        ],
        "Basic Materials": [
            "LIN", "APD", "ECL", "SHW", "DD", "NEM", "FCX", "NUE"
        ],
        "Real Estate": [
            "PLD", "AMT", "EQIX", "PSA", "WELL", "DLR", "O", "SPG"
        ],
        "Utilities": [
            "NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL"
        ]
    }

    #Get tickers for this sector
    sector_tickers = MAJOR_TICKERS_BY_SECTOR.get(sector, [])

    if not sector_tickers:
        #unknown sector, return empty
        return []
    
    #get info for each ticker in the sector
    competitors = []
    import time
    for comp_ticker in sector_tickers:
        #skip target company
        if comp_ticker == ticker:
            continue
        try:
            # Use cached ticker info to avoid rate limits
            comp_info = _get_cached_ticker_info(comp_ticker)
        
            #Get market cap
            comp_market_cap = comp_info.get('marketCap', 0)

            #Filter by similar market cap (0.3x to 3x)
            #This ensure we're comparing companies of similar size
            if target_market_cap > 0:
                ratio = comp_market_cap / target_market_cap
                if ratio < 0.3 or ratio > 3.0:
                    continue #too diffrent in size
            #Add to competitors list
            competitors.append({
                "ticker": comp_ticker,
                "name": comp_info.get('longName', comp_ticker),
                "market_cap": comp_market_cap,
                "industry": comp_info.get('industry', 'Unknown')
            })
        except Exception as e:
            #skip this ticker if there's an error
            continue
    # Sort by market cap (closest to target first) 
    if target_market_cap > 0:
        competitors.sort(
            key=lambda x: abs(x['market_cap'] - target_market_cap)
        )
    return competitors

def _get_cached_ticker_info(ticker: str) -> Dict[str, Any]:
    """
    Gets ticker info from cache or API with caching.
    This prevents rate limits by caching responses locally.
    
    Strategy:
    1. Check if cached data exists and is fresh (< 24 hours old)
    2. If cache exists and fresh, return cached data (no API call!)
    3. If cache missing or stale, fetch from API and cache it
    4. If API fails, try to use stale cache as fallback
    
    This ensures:
    - First run: Fetches from API and caches
    - Subsequent runs: Uses cache (no rate limits!)
    - Presentation: All data pre-cached, no API calls needed
    """
    cache_file = CACHE_DIR / f"ticker_{ticker}.json"
    
    # Check if cache exists and is fresh
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid (within duration)
            cache_time_str = cached_data.get('cached_at', '2000-01-01T00:00:00')
            try:
                cache_time = datetime.fromisoformat(cache_time_str.replace('Z', '+00:00').split('+')[0])
            except:
                cache_time = datetime.fromisoformat(cache_time_str.split('.')[0])
            
            age = datetime.now() - cache_time
            
            if age < timedelta(hours=CACHE_DURATION_HOURS):
                # Cache is fresh, use it!
                return cached_data.get('info', {})
        except Exception as e:
            # If cache read fails, continue to fetch fresh
            pass
    
    # Fetch fresh data from API
    try:
        target = yf.Ticker(ticker)
        target_info = target.info
        
        # Save to cache for future use
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'info': target_info,
                    'cached_at': datetime.now().isoformat()
                }, f, default=str)
        except:
            pass  # If cache write fails, continue anyway
        
        # Add delay to avoid rate limits
        time.sleep(0.5)
        
        return target_info
    except Exception as e:
        # If API fails, try to return stale cache as fallback
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    print(f"⚠️  Using cached data for {ticker} (API rate limited)")
                    return cached_data.get('info', {})
            except:
                pass
        raise e

def _create_error_result(ticker: str, error_msg: str) -> Dict[str, Any]:
    '''
    Creates a standardized error result

    Args:
        ticker: The ticker that failed
        error_msg: Description of what went wrong 
    Returns:
        ToolResult dict with error info
    '''
    return {
        "tool_name": "find_competitors",
        "parameters": {"ticker": ticker},
        "data": None,
        "source": "yfinance",
        "timestamp": datetime.utcnow().isoformat(),
        "confidence": 0.0,
        "success": False,
        "error": error_msg
    }

# FOR TESTING

if __name__ == "__main__":
    """
    Test the competitor finder with various companies.
    """
    
    test_tickers = [
        ("TSLA", "Tesla - should find Ford, GM, Rivian"),
        ("AAPL", "Apple - should find Microsoft, Google, Meta"),
        ("JPM", "JPMorgan - should find BAC, WFC, C")
    ]
    
    for ticker, description in test_tickers:
        print("=" * 70)
        print(f"Testing: {description}")
        print("=" * 70)
        
        # Add delay to avoid rate limits
        import time
        time.sleep(3)  # Wait 3 seconds between requests
        
        result = find_competitors(ticker)
        
        if result["success"]:
            data = result["data"]
            print(f"Target: {data['target_company']}")
            print(f"Sector: {data['sector']}")
            print(f"Industry: {data['industry']}")
            print(f"\nCompetitors found: {data['total_found']}")
            print("\nTop 5:")
            
            for i, comp in enumerate(data['competitors'][:5], 1):
                market_cap_b = comp['market_cap'] / 1_000_000_000
                print(f"{i}. {comp['ticker']}: {comp['name']} (${market_cap_b:.1f}B)")
        else:
            print(f"Error: {result['error']}")
        
        print("\n")