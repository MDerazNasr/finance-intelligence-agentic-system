"""
Pre-cache Competitor Data Script

Run this BEFORE your presentation to:
1. Test both Polygon and yfinance paths
2. Cache all demo data locally
3. Ensure zero API calls during demo

This makes your demo bulletproof - everything runs from cache.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from tools.competitor_finder import find_competitors
import time

# Companies you'll demo
DEMO_COMPANIES = [
    ("AAPL", 5, "Apple - Technology"),
    ("GOOGL", 5, "Google - Technology"),
    ("MSFT", 5, "Microsoft - Technology"),
    ("TSLA", 5, "Tesla - Auto Manufacturing"),
    ("JPM", 5, "JPMorgan - Banking"),
    ("UNH", 5, "UnitedHealth - Healthcare"),
]

print("=" * 80)
print("🔧 PRE-CACHING COMPETITOR DATA FOR DEMO")
print("=" * 80)
print("\nThis will:")
print("  1. Test Polygon.io integration (if API key set)")
print("  2. Test yfinance fallback")
print("  3. Cache all results locally")
print("  4. Make your demo instant (no API calls needed)")
print("\n" + "=" * 80)

# Check if Polygon API key is set
has_polygon = bool(os.getenv("POLYGON_API_KEY"))
if has_polygon:
    print("✅ Polygon API key detected - will test both sources")
else:
    print("⚠️  No Polygon API key - will use yfinance only")
    print("   To test Polygon: Add POLYGON_API_KEY to .env")

print("=" * 80)
print()

# Track statistics
polygon_success = 0
yfinance_success = 0
errors = 0

for ticker, limit, description in DEMO_COMPANIES:
    print(f"\n📊 Caching: {description}")
    print("-" * 80)
    
    try:
        result = find_competitors(ticker, limit=limit)
        
        if result['success']:
            data = result['data']
            source = data.get('data_source_used', 'unknown')
            
            if source == 'polygon':
                polygon_success += 1
                print(f"✅ Cached via Polygon.io - {data['total_found']} competitors found")
            elif source == 'yfinance':
                yfinance_success += 1
                print(f"✅ Cached via yfinance - {data['total_found']} competitors found")
            
            # Show top 3 competitors
            print("   Top 3 competitors:")
            for i, comp in enumerate(data['competitors'][:3], 1):
                cap = comp['market_cap'] / 1e9
                print(f"     {i}. {comp['ticker']}: {comp['name']} (${cap:.1f}B)")
        else:
            errors += 1
            print(f"❌ Error: {result['error']}")
    
    except Exception as e:
        errors += 1
        print(f"❌ Exception: {str(e)}")
    
    # Small delay between requests
    time.sleep(1)

# Summary
print("\n" + "=" * 80)
print("📊 PRE-CACHE SUMMARY")
print("=" * 80)
print(f"Total companies: {len(DEMO_COMPANIES)}")
print(f"Polygon.io success: {polygon_success}")
print(f"yfinance success: {yfinance_success}")
print(f"Errors: {errors}")

if errors == 0:
    print("\n✅ ALL DATA CACHED SUCCESSFULLY!")
    print("\n🎉 Your demo is ready!")
    print("   - All data is cached locally")
    print("   - No API calls during presentation")
    print("   - Instant responses guaranteed")
else:
    print(f"\n⚠️  {errors} errors occurred")
    print("   Check error messages above and retry")

print("\n" + "=" * 80)