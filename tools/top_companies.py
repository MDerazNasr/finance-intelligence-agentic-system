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
