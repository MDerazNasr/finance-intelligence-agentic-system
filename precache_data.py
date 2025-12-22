#!/usr/bin/env python3
"""
Pre-cache Data Script - Run this BEFORE your presentation!

This script pre-fetches and caches all the data you'll need during your demo,
so you won't hit rate limits during the presentation.

Usage:
    python precache_data.py

Run this once, wait for it to complete, then your presentation will use cached data!
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.competitor_finder import find_competitors
from tools.sec_analyzer import get_latest_quarterly_financials
import time

# Companies you'll demo during presentation
DEMO_TICKERS = [
    "AAPL",  # Apple
    "GOOGL", # Google
    "MSFT",  # Microsoft
    "TSLA",  # Tesla
    "JPM",   # JPMorgan
    "F",     # Ford
    "GM",    # General Motors
]

print("=" * 70)
print("🔧 PRE-CACHING DATA FOR PRESENTATION")
print("=" * 70)
print("\nThis will fetch and cache data for all demo companies.")
print("This ensures no rate limits during your presentation!\n")

# Pre-cache SEC financial data
print("📊 Caching SEC financial data...")
for ticker in DEMO_TICKERS:
    try:
        print(f"  Fetching {ticker}...", end=" ")
        result = get_latest_quarterly_financials(ticker)
        if result.get('success'):
            print("✅")
        else:
            print(f"⚠️  {result.get('error', 'Failed')}")
        time.sleep(1)  # Small delay
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")

print("\n🏢 Caching competitor data...")
# Pre-cache competitor data (this will cache all competitor tickers too)
for ticker in DEMO_TICKERS[:3]:  # Just cache top 3 to avoid too many requests
    try:
        print(f"  Fetching competitors for {ticker}...", end=" ")
        result = find_competitors(ticker)
        if result.get('success'):
            competitors = result.get('data', {}).get('competitors', [])
            print(f"✅ ({len(competitors)} competitors cached)")
        else:
            print(f"⚠️  {result.get('error', 'Failed')}")
        time.sleep(2)  # Longer delay for competitor lookups
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")

print("\n" + "=" * 70)
print("✅ PRE-CACHING COMPLETE!")
print("=" * 70)
print("\n✨ Your presentation is ready!")
print("   All data is cached and will be used instantly (no API calls).")
print("   Cache is valid for 24 hours.\n")

