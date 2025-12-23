"""
Top Companies Tool - Market Cap Rankings

Returns the top N companies in a given industry/sector ranked by market cap.

Why this is useful:
- "Who are the biggest players in healthcare?"
- "Top 10 tech companies by size"
- Comparative analysis across industries

Strategy:
1. Search S&P 500 universe (or use cached data)
2. Filter by sector/industry match
3. Sort by market cap (descending)
4. Return top N

Data source: yfinance (with caching)
Confidence: 0.8 (reliable market data)

uses cascading data sources:
1. polygon
2. yfinance (fallback)
"""
import os
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import requests #for POLYGON API
from dotenv import load_dotenv

#load env
load_dotenv()

#cache config
CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_DURATION_HOURS = 24

# Map common industry terms to GICS sectors
INDUSTRY_TO_SECTOR = {
    # Technology
    "technology": "Technology",
    "tech": "Technology",
    "software": "Technology",
    
    # Healthcare
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "pharma": "Healthcare",
    
    # Financial Services
    "finance": "Financial Services",
    "financial": "Financial Services",
    "banking": "Financial Services",
    
    # Consumer Cyclical
    "retail": "Consumer Cyclical",
    "automotive": "Consumer Cyclical",
    "auto": "Consumer Cyclical",
    
    # ... add more as needed
}


def get_top_companies(industry: str, n: int = 10) -> Dict[str, Any]:
    """
    Get top N companies in an industry by market cap.
    
    Uses cascading data sources:
    1. Polygon.io (primary)
    2. yfinance (fallback)
    
    Args:
        industry: Industry name (e.g., "technology", "healthcare")
        n: Number of companies to return (default: 10)
        
    Returns:
        ToolResult dict with companies ranked by market cap
    """

    start_time = time.time()

    #Step 1 - check cache
    cache_key = f"top_companies_{industry.lower()}"
    cached = _get_from_cache(cache_key)
    if cached:
        #Add minimum delay for consistency
        elapsed = time.time() - start_time
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)
        return cached
    #step 2 map industry to sector
    sector = INDUSTRY_TO_SECTOR.get(industry.lower())
    if not sector:
        return _create_error_result(
            industry, n,
            f"Unknown industry: '{industry}'. Try: technology, healthcare, finance, etc."
        )
    #Try Polygon (primary)
    polygon_api_key = os.getenv("POLYGON_API_KEY")

    if polygon_api_key:
        try:
            print(f"Trying Polygon.io")
            result = _fetch_from_polygon(industry, sector, n)

            if result['success']:
                print(f"Success via Polygon.io")
                result['data']['data_source_used'] = 'polygon'

                #Cache it
                _save_to_cache(cache_key, result)
                #Ensure min time delay
                elapsed = time.time() - start_time
                if elapsed < 0.5:
                    time.sleep(0.5 - elapsed)
                
                return result
            else:
                print(f"Polygon failed: {result.get('error')}")
        
        except Exception as e:
            print(f"Polygon error: {str(e)}")
    
    #Step 4 - Fall back to yfinance
    print(f"Falling back to yfinance")
    result = _fetch_from_yfinance(industry, sector, n)

    if result['success']:
        result['data']['data_source_used'] = 'yfinance'
        _save_to_cache(cache_key, result)
    
    elapsed = time.time() - start_time
    if elapsed < 0.5:
        time.sleep(0.5 - elapsed)
    
    return result

def _fetch_from_polygon(industry: str, sector: str, n: int) -> Dict[str, Any]:
    '''
        Fetch top companies using Polygon.io
    
    Algorithm:
    1. Get list of active US stock tickers from Polygon
    2. For each ticker, get sector info (might need yfinance for this)
    3. Filter to matching sector
    4. Get market caps
    5. Sort by market cap, return top N
    
    Challenge: Polygon doesn't have built-in sector filtering
    Solution: Hybrid approach - use Polygon for ticker list,
            yfinance for sector classification
    '''

    api_key = os.getenv("POLYOGON_API_KEY")

    try:
        #option A - get SNP 500 list via Poly.
        print(f"Getting S&P 500 universe...")

        #Verify each via Polygon to ensure they're valid
        companies = []
        for ticker in sp500_tickers:
            try:
                #Get ticker details from Polygon
                url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
                response = requests.get(url, params={"apiKey": api_key}, timeout=10)

                if response.status_code == 200:
                    ticker_data = response.json().get('results', {})

                    # Get sector from yfinance (Polygon doesn't have GICS sectors)
                    ticker_info = _get_cached_ticker_info(ticker)
                    ticker_sector = ticker_info.get('sector', '')

                    #Filter by sector
                    if ticker_sector == sector:
                        companies.append({
                            'ticker': ticker,
                            'name': ticker_data.get('name', ticker),
                            'market_cap': ticker_info.get('marketCap', 0)
                        })
                time.sleep(0.1) #Rate limiting
            except:
                continue

            #Sort by market cap
            companies.sort(key=lambda x: x['market_cap'], reverse=True)

            #Return top N
            return {
                'success': True,
                'data': {
                    'industry_query': industry,
                    'sector': sector,
                    'companies': companies[:n],
                    'total_in_sector': len(companies)
                },
                'source': 'Polygon.io + yfinance',
                'confidence': 0.85
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def _fetch_from_yfinance(industry: str, sector: str, n: int) -> Dict[str, Any]:
    """
    Fallback: Use yfinance for everything
    
    Algorithm:
    1. Get S&P 500 ticker list
    2. For each ticker, get info from yfinance
    3. Filter by sector match
    4. Sort by market cap
    5. Return top N
    """
    
    try:
        import yfinance as yf
        
        print(f"    📋 Getting S&P 500 companies...")
        sp500_tickers = _get_sp500_universe()
        
        companies = []
        
        for ticker in sp500_tickers:
            try:
                info = _get_cached_ticker_info(ticker)
                
                # Check sector match
                if info.get('sector') == sector:
                    market_cap = info.get('marketCap', 0)
                    if market_cap > 0:
                        companies.append({
                            'ticker': ticker,
                            'name': info.get('longName', ticker),
                            'market_cap': market_cap
                        })
            except:
                continue
        
        # Sort by market cap descending
        companies.sort(key=lambda x: x['market_cap'], reverse=True)
        
        return {
            'success': True,
            'data': {
                'industry_query': industry,
                'sector': sector,
                'companies': companies[:n],
                'total_in_sector': len(companies)
            },
            'source': 'yfinance',
            'confidence': 0.8,
            'tool_name': 'get_top_companies',
            'parameters': {'industry': industry, 'n': n},
            'timestamp': datetime.utcnow().isoformat(),
            'error': None
        }
    
    except Exception as e:
        return _create_error_result(industry, n, str(e))