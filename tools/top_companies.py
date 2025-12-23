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
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf #for yfinance
import requests #for POLYGON API
from dotenv import load_dotenv

#load env
load_dotenv()

# Demo flag: force yfinance-only (skip Polygon) for speed/offline demos
DEMO_YFINANCE_ONLY = os.getenv("DEMO_YFINANCE_ONLY", "").lower() == "true"



#cache config
CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_DURATION_HOURS = 24

# Rate limit tracking (to avoid hammering APIs)
class RateLimiter:
    """Simple rate limiter to track API calls"""
    def __init__(self):
        self.polygon_calls = []
        self.yfinance_calls = []
    
    def can_call_polygon(self) -> bool:
        """Check if we can call Polygon (5 per minute limit)"""
        now = datetime.now()
        # Remove calls older than 1 minute
        self.polygon_calls = [t for t in self.polygon_calls if now - t < timedelta(minutes=1)]
        return len(self.polygon_calls) < 5
    
    def record_polygon_call(self):
        """Record a Polygon API call"""
        self.polygon_calls.append(datetime.now())
    
    def record_yfinance_call(self):
        """Record a yfinance call"""
        self.yfinance_calls.append(datetime.now())

rate_limiter = RateLimiter()

# Map common industry terms to GICS sectors
INDUSTRY_TO_SECTOR = {
    # Technology
    "technology": "Technology",
    "tech": "Technology",
    "software": "Technology",
    "hardware": "Technology",
    "semiconductors": "Technology",
    "it": "Technology",

    # Healthcare
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "pharma": "Healthcare",
    "biotech": "Healthcare",
    "medical": "Healthcare",

    # Financials
    "finance": "Financial Services",
    "financial": "Financial Services",
    "banking": "Financial Services",
    "banks": "Financial Services",
    "insurance": "Financial Services",
    "fintech": "Financial Services",

    # Consumer Discretionary (Cyclical)
    "consumer cyclical": "Consumer Cyclical",
    "retail": "Consumer Cyclical",
    "automotive": "Consumer Cyclical",
    "auto": "Consumer Cyclical",
    "e-commerce": "Consumer Cyclical",
    "apparel": "Consumer Cyclical",
    "hotels": "Consumer Cyclical",

    # Consumer Staples (Defensive)
    "consumer defensive": "Consumer Defensive",
    "staples": "Consumer Defensive",
    "food": "Consumer Defensive",
    "beverages": "Consumer Defensive",
    "tobacco": "Consumer Defensive",
    "household products": "Consumer Defensive",

    # Communication Services
    "communication": "Communication Services",
    "telecom": "Communication Services",
    "media": "Communication Services",
    "entertainment": "Communication Services",
    "social media": "Communication Services",

    # Energy
    "energy": "Energy",
    "oil": "Energy",
    "gas": "Energy",
    "drilling": "Energy",
    "renewables": "Energy",

    # Industrials
    "industrials": "Industrials",
    "aerospace": "Industrials",
    "defense": "Industrials",
    "manufacturing": "Industrials",
    "transportation": "Industrials",
    "logistics": "Industrials",

    # Materials
    "materials": "Materials",
    "mining": "Materials",
    "chemicals": "Materials",
    "steel": "Materials",
    "lumber": "Materials",

    # Real Estate
    "real estate": "Real Estate",
    "reit": "Real Estate",
    "property": "Real Estate",

    # Utilities
    "utilities": "Utilities",
    "electric": "Utilities",
    "water": "Utilities",
    "power": "Utilities"
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
    #Try Polygon (primary) unless demo flag forces yfinance
    polygon_api_key = os.getenv("POLYGON_API_KEY")

    if polygon_api_key and not DEMO_YFINANCE_ONLY:
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
    else:
        if DEMO_YFINANCE_ONLY:
            print("Polygon skipped (DEMO_YFINANCE_ONLY=true); using yfinance")
    
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

    api_key = os.getenv("POLYGON_API_KEY")

    try:
        #option A - get S&P 500 list (cached)
        print(f"Getting S&P 500 universe...")
        sp500_tickers = _get_sp500_universe()

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
    
def _get_sp500_universe() -> List[str]:
    """Get S&P 500 ticker list (cached 30 days)"""
    # Implementation here - fetches from Wikipedia
    # Falls back to hardcoded list
    # Same as competitor_finder
    cache_file = CACHE_DIR / "sp500_universe.json"
    
    # Check cache (valid for 30 days)
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            
            cache_time = datetime.fromisoformat(cached['cached_at'])
            if datetime.now() - cache_time < timedelta(days=30):
                return cached['tickers']
        except:
            pass
    
    # Fetch from Wikipedia with proper headers to avoid 403 errors
    try:
        import pandas as pd
        import requests
        
        print("    📥 Fetching S&P 500 list from Wikipedia...")
        
        # Use requests with proper headers to avoid 403 Forbidden
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Fetch the page with headers
        response = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML with pandas (using StringIO to avoid deprecation warning)
        from io import StringIO
        table = pd.read_html(StringIO(response.text))[0]
        tickers = table['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]
        
        # Cache it
        with open(cache_file, 'w') as f:
            json.dump({
                'tickers': tickers,
                'cached_at': datetime.now().isoformat()
            }, f)
        
        print(f"    ✅ Loaded {len(tickers)} S&P 500 companies")
        return tickers
    except Exception as e:
        print(f"    ⚠️ Failed to fetch S&P 500 list: {e}")
        # Comprehensive fallback list - all S&P 500 Technology companies + major companies
        # This ensures we have complete coverage even if Wikipedia fails
        return [
            # Technology (S&P 500) - comprehensive list
            "AAPL", "MSFT", "GOOGL", "GOOG", "META", "NVDA", "AVGO", "ORCL", "ADBE", "CRM", 
            "CSCO", "ACN", "AMD", "INTC", "IBM", "QCOM", "TXN", "SHOP", "NOW", "INTU",
            "AMAT", "LRCX", "KLAC", "SNPS", "CDNS", "ANSS", "FTNT", "PANW", "CRWD", "ZS",
            "NET", "DDOG", "MDB", "TEAM", "ESTC", "DOCN", "FROG", "GTLB", "ASAN", "VEEV",
            "WDAY", "ZM", "DOCU", "COUP", "OKTA", "SPLK", "QLYS", "VRSN", "FFIV", "AKAM",
            # Consumer Cyclical
            "AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "TM", "F", "GM", "BKNG", "LOW", "TGT", "ABNB", "MAR", "RIVN", "LCID", "EBAY",
            # Healthcare
            "UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "PFE", "DHR", "BMY", "AMGN", "CVS", "CI", "ELV", "HCA", "ISRG",
            # Financial Services
            "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "SPGI", "BLK", "C", "AXP", "CB", "PGR", "MMC", "SCHW",
            # Communication Services
            "NFLX", "DIS", "CMCSA", "TMUS", "VZ", "T",
            # Consumer Defensive
            "WMT", "PG", "COST", "KO", "PEP", "PM", "MO", "EL", "CL", "KMB",
            # Energy
            "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY",
            # Industrials
            "UPS", "RTX", "HON", "UNP", "BA", "CAT", "GE", "LMT", "DE", "MMM",
            # Basic Materials
            "LIN", "APD", "ECL", "SHW", "DD", "NEM", "FCX", "NUE",
            # Real Estate
            "PLD", "AMT", "EQIX", "PSA", "WELL", "DLR", "O", "SPG",
            # Utilities
            "NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL"
        ]

def _get_cached_ticker_info(ticker: str) -> Dict[str, Any]:
    """Get ticker info from yfinance (cached 24 hours)"""
    # Implementation here - fetches from yfinance
    # Caches locally
    """Get ticker info from yfinance with 24-hour caching"""
    
    cache_file = CACHE_DIR / f"ticker_{ticker}.json"
    
    # Try cache first
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cached_data['cached_at'])
            age = datetime.now() - cache_time
            
            if age < timedelta(hours=CACHE_DURATION_HOURS):
                return cached_data['info']
        except:
            pass
    
    # Fetch from yfinance
    try:
        rate_limiter.record_yfinance_call()
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Cache it
        with open(cache_file, 'w') as f:
            json.dump({
                'info': info,
                'cached_at': datetime.now().isoformat()
            }, f, default=str)
        
        time.sleep(0.1)  # Small delay to respect rate limits
        return info
    
    except Exception as e:
        # Try stale cache as last resort
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                return cached_data['info']
            except:
                pass
        raise e

def _get_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Read from cache if fresh"""
    """Get result from cache if valid"""
    
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            
            cache_time = datetime.fromisoformat(cached['cached_at'])
            age = datetime.now() - cache_time
            
            if age < timedelta(hours=CACHE_DURATION_HOURS):
                return cached['result']
        except:
            pass
    
    return None

def _save_to_cache(cache_key: str, data: Dict):
    """Write to cache"""
    """Save result to cache"""
    
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    try:
        with open(cache_file, 'w') as f:
            json.dump({
                'result': result,
                'cached_at': datetime.now().isoformat()
            }, f, default=str)
    except:
        pass  # Don't fail if cache write fails


def _create_error_result(ticker: str, error_msg: str) -> Dict[str, Any]:
    """Create standardized error result"""
    
    return {
        "tool_name": "find_competitors",
        "parameters": {"ticker": ticker},
        "data": None,
        "source": "competitor_finder",
        "timestamp": datetime.utcnow().isoformat(),
        "confidence": 0.0,
        "success": False,
        "error": error_msg
    }

def _create_error_result(industry: str, n: int, error: str) -> Dict:
    """Standard error format"""
    return {
        'tool_name': 'get_top_companies',
        'parameters': {'industry': industry, 'n': n},
        'success': False,
        'confidence': 0.0,
        'error': error,
        'data': None
    }