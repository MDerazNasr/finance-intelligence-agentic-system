#!/usr/bin/env python3
"""
Simple script to get ticker sectors from cached data or generate a list.

This script:
1. Reads from your existing cache files (.cache/ticker_*.json)
2. Groups tickers by sector
3. Outputs formatted Python dict for copy-paste into competitor_finder.py

Usage:
    python scripts/get_ticker_sectors.py
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CACHE_DIR = PROJECT_ROOT / ".cache"

def get_tickers_from_cache():
    """Read all cached ticker files and extract sector info."""
    sectors_dict = defaultdict(list)
    
    if not CACHE_DIR.exists():
        print("⚠️  No cache directory found. Run competitor_finder.py first to populate cache.")
        return sectors_dict
    
    cache_files = list(CACHE_DIR.glob("ticker_*.json"))
    print(f"Found {len(cache_files)} cached ticker files\n")
    
    for cache_file in cache_files:
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            info = data.get('info', {})
            ticker = cache_file.stem.replace('ticker_', '').upper()
            sector = info.get('sector', 'Unknown')
            
            if sector and sector != 'Unknown':
                sectors_dict[sector].append(ticker)
        except Exception as e:
            continue
    
    return sectors_dict

def format_for_python(sectors_dict):
    """Format sectors dict as Python code."""
    # Standard GICS sectors (in order)
    standard_sectors = [
        "Technology",
        "Consumer Cyclical",
        "Healthcare",
        "Financial Services",
        "Communication Services",
        "Consumer Defensive",
        "Energy",
        "Industrials",
        "Basic Materials",
        "Real Estate",
        "Utilities"
    ]
    
    print("MAJOR_TICKERS_BY_SECTOR = {")
    
    for sector in standard_sectors:
        tickers = sorted(set(sectors_dict.get(sector, [])))  # Remove duplicates, sort
        if tickers:
            print(f'    "{sector}": [')
            # Format with 8 tickers per line
            for i in range(0, len(tickers), 8):
                line_tickers = tickers[i:i+8]
                comma = ',' if i+8 < len(tickers) else ''
                print('        "' + '", "'.join(line_tickers) + '"' + comma)
            print('    ],')
    
    # Print any sectors not in standard list
    other_sectors = set(sectors_dict.keys()) - set(standard_sectors)
    if other_sectors:
        print("\n    # Additional sectors found:")
        for sector in sorted(other_sectors):
            tickers = sorted(set(sectors_dict.get(sector, [])))
            print(f'    "{sector}": {tickers},')
    
    print("}")

def main():
    print("=" * 80)
    print("TICKER SECTOR LIST GENERATOR")
    print("=" * 80)
    print("\nReading from cache files...")
    
    sectors_dict = get_tickers_from_cache()
    
    if not sectors_dict:
        print("\n❌ No sector data found in cache.")
        print("\nTo populate cache, run:")
        print("  python tools/competitor_finder.py")
        print("\nOr manually fetch tickers using:")
        print("  python -c \"import yfinance as yf; print(yf.Ticker('AAPL').info.get('sector'))\"")
        return
    
    print(f"\n✅ Found {sum(len(tickers) for tickers in sectors_dict.values())} tickers across {len(sectors_dict)} sectors\n")
    
    print("=" * 80)
    print("FORMATTED OUTPUT (copy-paste into competitor_finder.py lines 187-224)")
    print("=" * 80)
    print()
    
    format_for_python(sectors_dict)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for sector in sorted(sectors_dict.keys()):
        count = len(sectors_dict[sector])
        print(f"{sector}: {count} tickers")

if __name__ == "__main__":
    main()

