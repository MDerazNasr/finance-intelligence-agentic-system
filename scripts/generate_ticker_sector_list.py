#!/usr/bin/env python3
"""
Generate a comprehensive ticker/sector list from S&P 500 companies.

This script fetches all S&P 500 tickers and their sectors from yfinance,
then formats them for easy copy-paste into competitor_finder.py

Usage:
    python scripts/generate_ticker_sector_list.py > ticker_sector_list.txt
"""

import yfinance as yf
import time
from collections import defaultdict
from typing import Dict, List

def get_sp500_tickers():
    """Get list of S&P 500 ticker symbols."""
    try:
        # Use yfinance to get S&P 500 tickers
        import pandas as pd
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        tickers = table['Symbol'].tolist()
        # Clean up tickers (remove dots, handle special cases)
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        return tickers
    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        print("Falling back to manual list...")
        # Fallback: return a curated list of major tickers
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
            "UNH", "XOM", "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "ABBV",
            "MRK", "COST", "AVGO", "ADBE", "WMT", "CRM", "NFLX", "DIS", "BAC",
            "ACN", "TMO", "LIN", "ABT", "DHR", "NKE", "VZ", "TXN", "BMY",
            "PM", "RTX", "UPS", "QCOM", "NEE", "MS", "HON", "AMGN", "SPGI",
            "LOW", "INTU", "AXP", "BKNG", "GE", "AMT", "SYK", "DE", "C",
            "ADI", "TJX", "ZTS", "CL", "ADP", "FI", "ISRG", "CMCSA", "ICE",
            "DUK", "SLB", "SO", "ITW", "MO", "EQIX", "SHW", "ETN", "HCA",
            "NOC", "PSA", "APH", "AON", "APD", "FCX", "EMR", "CME", "CPRT",
            "MCK", "CDNS", "CTSH", "AFL", "MCHP", "APH", "FAST", "FTV", "FTNT"
        ]

def fetch_ticker_sector(ticker: str) -> Dict[str, str]:
    """Fetch sector and industry for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', 'Unknown')
        industry = info.get('industry', 'Unknown')
        market_cap = info.get('marketCap', 0)
        return {
            'ticker': ticker,
            'sector': sector,
            'industry': industry,
            'market_cap': market_cap
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'market_cap': 0,
            'error': str(e)
        }

def main():
    print("Fetching S&P 500 tickers...")
    tickers = get_sp500_tickers()
    print(f"Found {len(tickers)} tickers")
    
    print("\nFetching sector information (this may take a few minutes)...")
    print("(Rate limited to avoid API throttling)\n")
    
    ticker_data = []
    sectors_dict = defaultdict(list)
    
    for i, ticker in enumerate(tickers, 1):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(tickers)} ({i*100//len(tickers)}%)")
        
        data = fetch_ticker_sector(ticker)
        ticker_data.append(data)
        
        sector = data['sector']
        if sector != 'Unknown':
            sectors_dict[sector].append(ticker)
        
        # Rate limiting
        time.sleep(0.2)
    
    print(f"\n✅ Fetched data for {len(ticker_data)} tickers\n")
    
    # Print formatted output for copy-paste
    print("=" * 80)
    print("FORMATTED OUTPUT FOR competitor_finder.py")
    print("=" * 80)
    print("\nMAJOR_TICKERS_BY_SECTOR = {")
    
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
    
    for sector in standard_sectors:
        tickers_in_sector = sectors_dict.get(sector, [])
        if tickers_in_sector:
            # Sort by market cap (largest first) - approximate by ticker order
            print(f'    "{sector}": [')
            # Format with 8 tickers per line
            ticker_lines = []
            for i in range(0, len(tickers_in_sector), 8):
                line_tickers = tickers_in_sector[i:i+8]
                ticker_lines.append('        "' + '", "'.join(line_tickers) + '"')
            
            for line in ticker_lines:
                if line == ticker_lines[-1]:
                    print(line)
                else:
                    print(line + ',')
            print('    ],')
    
    # Print any sectors not in standard list
    other_sectors = set(sectors_dict.keys()) - set(standard_sectors)
    if other_sectors:
        print("\n    # Additional sectors found:")
        for sector in sorted(other_sectors):
            tickers_in_sector = sectors_dict.get(sector, [])
            print(f'    "{sector}": {tickers_in_sector},')
    
    print("}\n")
    
    # Print summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    for sector in standard_sectors:
        count = len(sectors_dict.get(sector, []))
        if count > 0:
            print(f"{sector}: {count} tickers")
    
    unknown_count = len([d for d in ticker_data if d['sector'] == 'Unknown'])
    if unknown_count > 0:
        print(f"Unknown: {unknown_count} tickers")
    
    # Print tickers with errors
    error_tickers = [d for d in ticker_data if 'error' in d]
    if error_tickers:
        print(f"\n⚠️  {len(error_tickers)} tickers had errors:")
        for d in error_tickers[:10]:  # Show first 10
            print(f"  - {d['ticker']}: {d.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()

