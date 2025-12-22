"""
Competitor Finder Tool - Cascading Data Sources with Graceful Degradation

This tool uses a production-grade architecture with multiple data sources:

Primary: Polygon.io (professional financial API)
- Industry-standard data provider
- Used by real fintech companies
- Real-time, high-quality data
- Rate limited on free tier (5/min, 250/day)

Fallback: yfinance (Yahoo Finance)
- Free and unlimited
- Reliable for development
- 15-minute delayed data
- Never fails

Pattern: "Graceful Degradation"
If Polygon fails (rate limit, API error, timeout), automatically
switch to yfinance. User always gets an answer.

This is how real financial systems work:
- Bloomberg Terminal: Multiple data feeds with automatic failover
- Trading platforms: Backup market data providers
- Payment systems: Redundant processors

Interview talking point:
"I built redundancy into the system from day one. If the primary
 data source fails, we seamlessly switch to backup. The user still
 gets their answer - they might not even notice we switched providers.
 This is standard practice in production financial systems."
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

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


# ============================================================================
# EXCEPTIONS
# ============================================================================

class RateLimitException(Exception):
    """Raised when API rate limit is hit"""
    pass

class PolygonAPIException(Exception):
    """Raised when Polygon API fails"""
    pass


# ============================================================================
# MAIN FUNCTION - CASCADING DATA SOURCES
# ============================================================================

def find_competitors(ticker: str, limit: int = 5) -> Dict[str, Any]:
    """
    Find competitors using cascading data sources.
    
    Flow:
    1. Try Polygon.io (if API key available)
       - Professional, real-time data
       - Rate limited but cached
    2. Fall back to yfinance (if Polygon fails)
       - Always reliable
       - Free and unlimited
    
    Args:
        ticker: Stock ticker symbol (e.g., "TSLA")
        limit: Maximum number of competitors to return (default: 5)
        
    Returns:
        ToolResult with competitor data and metadata about which source was used
        
    Example result:
        {
            "success": True,
            "data": {
                "competitors": [...],
                "data_source_used": "polygon",  # or "yfinance"
                "fallback_reason": None  # or reason if fallback happened
            },
            "confidence": 0.85,  # 0.85 for Polygon, 0.8 for yfinance
            ...
        }
    """
    
    print(f"\n🔍 Finding competitors for {ticker} (limit: {limit})...")
    
    data_source_used = None
    fallback_reason = None
    result = None
    
    # ========================================================================
    # STEP 1: Try Polygon.io (Primary Source)
    # ========================================================================
    
    if _has_polygon_api_key():
        print("  📊 Attempting Polygon.io (professional API)...")
        
        try:
            # Check rate limit before calling
            if not rate_limiter.can_call_polygon():
                raise RateLimitException("Polygon rate limit: 5 calls/minute exceeded")
            
            result = _fetch_from_polygon(ticker, limit)
            
            if result['success']:
                print("  ✅ Success via Polygon.io")
                result['data']['data_source_used'] = 'polygon'
                result['data']['fallback_reason'] = None
                result['confidence'] = 0.85  # Slightly higher than yfinance
                return result
            else:
                fallback_reason = f"Polygon returned error: {result.get('error', 'Unknown')}"
                print(f"  ⚠️ Polygon failed: {fallback_reason}")
        
        except RateLimitException as e:
            fallback_reason = f"Polygon rate limit: {str(e)}"
            print(f"  ⚠️ {fallback_reason}")
        
        except PolygonAPIException as e:
            fallback_reason = f"Polygon API error: {str(e)}"
            print(f"  ⚠️ {fallback_reason}")
        
        except Exception as e:
            fallback_reason = f"Polygon unexpected error: {str(e)}"
            print(f"  ⚠️ {fallback_reason}")
    else:
        fallback_reason = "No Polygon API key configured (set POLYGON_API_KEY in .env)"
        print(f"  ℹ️ {fallback_reason}")
    
    # ========================================================================
    # STEP 2: Fallback to yfinance (Backup Source)
    # ========================================================================
    
    print(f"  🔄 Falling back to yfinance...")
    print(f"     Reason: {fallback_reason}")
    
    try:
        result = _fetch_from_yfinance(ticker, limit)
        
        if result['success']:
            print("  ✅ Success via yfinance (fallback)")
            result['data']['data_source_used'] = 'yfinance'
            result['data']['fallback_reason'] = fallback_reason
            result['confidence'] = 0.8  # Standard yfinance confidence
            return result
        else:
            # Both sources failed - return the yfinance error
            print("  ❌ yfinance also failed")
            return result
    
    except Exception as e:
        print(f"  ❌ yfinance failed: {str(e)}")
        return _create_error_result(
            ticker, 
            f"All data sources failed. Polygon: {fallback_reason}, yfinance: {str(e)}"
        )


# ============================================================================
# POLYGON.IO INTEGRATION
# ============================================================================

def _fetch_from_polygon(ticker: str, limit: int) -> Dict[str, Any]:
    """
    Fetch competitors using Polygon.io API.
    
    Polygon.io provides:
    - Professional-grade financial data
    - Real-time market information
    - SIC code classification for industry grouping
    - Comprehensive company reference data
    
    Free tier limits:
    - 5 API calls per minute
    - 250 API calls per day
    - 15-minute delayed data
    
    Strategy:
    1. Get target company's SIC code (industry classification)
    2. Search for companies with same SIC code
    3. Filter by market cap similarity
    4. Cache results aggressively (24 hours)
    
    Note: We're using the free tier for demo. In production, you'd
    use the paid tier (1000 calls/min, real-time data, $200/month).
    """
    
    try:
        import requests
        
        api_key = os.getenv("POLYGON_API_KEY")
        if not api_key:
            raise PolygonAPIException("POLYGON_API_KEY not found in environment")
        
        # Check cache first
        cache_key = f"polygon_competitors_{ticker}_{limit}"
        cached = _get_from_cache(cache_key)
        if cached:
            print("    💾 Using cached Polygon data")
            return cached
        
        # ====================================================================
        # Step 1: Get target company details
        # ====================================================================
        
        rate_limiter.record_polygon_call()
        
        ticker_url = f"https://api.polygon.io/v3/reference/tickers/{ticker.upper()}"
        response = requests.get(ticker_url, params={"apiKey": api_key}, timeout=10)
        
        if response.status_code == 429:
            raise RateLimitException("Polygon rate limit exceeded")
        elif response.status_code != 200:
            raise PolygonAPIException(f"Polygon API returned {response.status_code}")
        
        target_data = response.json().get('results', {})
        
        company_name = target_data.get('name', ticker.upper())
        sic_code = target_data.get('sic_code')
        market_cap = target_data.get('market_cap', 0)
        
        if not sic_code:
            raise PolygonAPIException(f"No SIC code found for {ticker}")
        
        print(f"    📋 {company_name} (SIC: {sic_code})")
        
        # ====================================================================
        # Step 2: Search for companies with same SIC code
        # ====================================================================
        
        # Small delay to respect rate limits
        time.sleep(0.2)
        rate_limiter.record_polygon_call()
        
        search_url = "https://api.polygon.io/v3/reference/tickers"
        search_params = {
            "sic_code": sic_code,
            "active": "true",
            "market": "stocks",
            "limit": 50,  # Get more, then filter
            "apiKey": api_key
        }
        
        response = requests.get(search_url, params=search_params, timeout=10)
        
        if response.status_code == 429:
            raise RateLimitException("Polygon rate limit exceeded")
        elif response.status_code != 200:
            raise PolygonAPIException(f"Polygon search returned {response.status_code}")
        
        results = response.json().get('results', [])
        
        # ====================================================================
        # Step 3: Filter and format competitors
        # ====================================================================
        
        competitors = []
        
        for comp in results:
            comp_ticker = comp.get('ticker', '').upper()
            
            # Skip target company
            if comp_ticker == ticker.upper():
                continue
            
            comp_name = comp.get('name', comp_ticker)
            comp_market_cap = comp.get('market_cap', 0)
            
            # Filter by market cap similarity (0.3x to 3x)
            if market_cap > 0 and comp_market_cap > 0:
                ratio = comp_market_cap / market_cap
                if ratio < 0.3 or ratio > 3.0:
                    continue
            
            competitors.append({
                "ticker": comp_ticker,
                "name": comp_name,
                "market_cap": comp_market_cap,
                "industry": comp.get('primary_exchange', 'Unknown')
            })
        
        # Sort by market cap similarity
        if market_cap > 0:
            competitors.sort(key=lambda x: abs(x['market_cap'] - market_cap))
        
        # ====================================================================
        # Step 4: Build result
        # ====================================================================
        
        data = {
            "target_company": company_name,
            "target_ticker": ticker.upper(),
            "sector": target_data.get('market', 'Unknown'),
            "industry": f"SIC {sic_code}",
            "target_market_cap": market_cap,
            "competitors": competitors[:limit],
            "total_found": len(competitors)
        }
        
        result = {
            "tool_name": "find_competitors",
            "parameters": {"ticker": ticker, "limit": limit},
            "data": data,
            "source": "Polygon.io professional API",
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.85,
            "success": True,
            "error": None
        }
        
        # Cache the result
        _save_to_cache(cache_key, result)
        
        return result
    
    except (RateLimitException, PolygonAPIException):
        # Re-raise these so caller knows it's a Polygon-specific issue
        raise
    
    except Exception as e:
        # Wrap other exceptions
        raise PolygonAPIException(f"Unexpected error: {str(e)}")


# ============================================================================
# YFINANCE INTEGRATION (FALLBACK)
# ============================================================================

def _fetch_from_yfinance(ticker: str, limit: int) -> Dict[str, Any]:
    """
    Fetch competitors using yfinance (Yahoo Finance).
    
    yfinance provides:
    - Free, unlimited access
    - Comprehensive US stock data
    - Sector and industry classifications
    - Market cap data
    
    Limitations:
    - Unofficial API (web scraper)
    - 15-minute delayed data
    - No SLA or support
    - Could break if Yahoo changes site
    
    Strategy:
    1. Get target company's sector/industry
    2. Search S&P 500 universe dynamically
    3. Filter by sector match + market cap similarity
    4. Cache aggressively (24 hours)
    
    This is reliable enough for POC/demo but would be replaced
    with professional API in production.
    """
    
    try:
        # Check cache first
        cache_key = f"yfinance_competitors_{ticker}_{limit}"
        cached = _get_from_cache(cache_key)
        if cached:
            print("    💾 Using cached yfinance data")
            return cached
        
        # ====================================================================
        # Step 1: Get target company info
        # ====================================================================
        
        target_info = _get_cached_ticker_info(ticker.upper())
        
        if not target_info or 'sector' not in target_info:
            return _create_error_result(
                ticker,
                "Could not retrieve company information from yfinance"
            )
        
        company_name = target_info.get('longName', ticker.upper())
        sector = target_info.get('sector', 'Unknown')
        industry = target_info.get('industry', 'Unknown')
        target_market_cap = target_info.get('marketCap', 0)
        
        print(f"    📋 {company_name}")
        print(f"       Sector: {sector}, Industry: {industry}")
        
        # ====================================================================
        # Step 2: Get S&P 500 universe
        # ====================================================================
        
        sp500_tickers = _get_sp500_universe()
        print(f"    🔍 Searching {len(sp500_tickers)} companies...")
        
        # ====================================================================
        # Step 3: Search for competitors dynamically
        # ====================================================================
        
        competitors = []
        checked = 0
        
        for comp_ticker in sp500_tickers:
            if comp_ticker == ticker.upper():
                continue
            
            try:
                comp_info = _get_cached_ticker_info(comp_ticker)
                checked += 1
                
                comp_sector = comp_info.get('sector', 'Unknown')
                comp_industry = comp_info.get('industry', 'Unknown')
                comp_market_cap = comp_info.get('marketCap', 0)
                
                # Filter by sector
                if comp_sector != sector:
                    continue
                
                # Filter by market cap similarity
                if target_market_cap > 0 and comp_market_cap > 0:
                    ratio = comp_market_cap / target_market_cap
                    
                    # Same industry: lenient (0.1x to 10x)
                    # Different industry: strict (0.3x to 3x)
                    if comp_industry == industry:
                        if ratio < 0.1 or ratio > 10:
                            continue
                    else:
                        if ratio < 0.3 or ratio > 3:
                            continue
                
                competitors.append({
                    "ticker": comp_ticker,
                    "name": comp_info.get('longName', comp_ticker),
                    "market_cap": comp_market_cap,
                    "industry": comp_industry,
                    "sector": comp_sector
                })
                
            except:
                continue
        
        # Sort by market cap similarity
        if target_market_cap > 0:
            competitors.sort(key=lambda x: abs(x['market_cap'] - target_market_cap))
        
        print(f"    ✅ Found {len(competitors)} competitors (checked {checked} companies)")
        
        # ====================================================================
        # Step 4: Build result
        # ====================================================================
        
        data = {
            "target_company": company_name,
            "target_ticker": ticker.upper(),
            "sector": sector,
            "industry": industry,
            "target_market_cap": target_market_cap,
            "competitors": competitors[:limit],
            "total_found": len(competitors)
        }
        
        result = {
            "tool_name": "find_competitors",
            "parameters": {"ticker": ticker, "limit": limit},
            "data": data,
            "source": "yfinance (Yahoo Finance)",
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.8,
            "success": True,
            "error": None
        }
        
        # Cache the result
        _save_to_cache(cache_key, result)
        
        return result
    
    except Exception as e:
        return _create_error_result(ticker, f"yfinance error: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _has_polygon_api_key() -> bool:
    """Check if Polygon API key is configured"""
    return bool(os.getenv("POLYGON_API_KEY"))


def _get_sp500_universe() -> List[str]:
    """
    Get S&P 500 ticker list (cached).
    
    Why S&P 500?
    - Standard benchmark index (not arbitrary list)
    - Covers major US companies (~$40T market cap)
    - Publicly available list
    - Updates quarterly (not daily)
    
    This is the ONE acceptable "list" because:
    - It's a real financial index, not our invention
    - We still fetch company data dynamically via API
    - We do sector matching via API, not hardcoding
    """
    
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
    
    # Fetch from Wikipedia
    try:
        import pandas as pd
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        tickers = table['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]
        
        # Cache it
        with open(cache_file, 'w') as f:
            json.dump({
                'tickers': tickers,
                'cached_at': datetime.now().isoformat()
            }, f)
        
        return tickers
    except:
        # Minimal fallback list
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
            "BRK-B", "UNH", "JNJ", "JPM", "V", "PG", "XOM", "HD"
        ]


def _get_cached_ticker_info(ticker: str) -> Dict[str, Any]:
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


def _save_to_cache(cache_key: str, result: Dict[str, Any]):
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


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test both Polygon and yfinance paths"""
    
    test_cases = [
        ("TSLA", 5, "Tesla"),
        ("AAPL", 10, "Apple"),
        ("JPM", 5, "JPMorgan"),
    ]
    
    for ticker, limit, description in test_cases:
        print("\n" + "=" * 80)
        print(f"TEST: {description} (limit: {limit})")
        print("=" * 80)
        
        result = find_competitors(ticker, limit=limit)
        
        if result['success']:
            data = result['data']
            source = data.get('data_source_used', 'unknown')
            fallback = data.get('fallback_reason')
            
            print(f"\n✅ Success via {source.upper()}")
            if fallback:
                print(f"   Fallback reason: {fallback}")
            
            print(f"\n   Target: {data['target_company']}")
            print(f"   Found {data['total_found']} competitors")
            print(f"\n   Top {limit}:")
            
            for i, comp in enumerate(data['competitors'], 1):
                cap = comp['market_cap'] / 1e9
                print(f"   {i}. {comp['ticker']}: {comp['name']} (${cap:.1f}B)")
        else:
            print(f"\n❌ Error: {result['error']}")
        
        print()
        time.sleep(1)  # Delay between tests