"""
Quick test script for top_companies tool
"""

import os
import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set environment variables
os.environ['SEC_API_USER_AGENT'] = 'Test test@example.com'
# Optional: Set Polygon key to test primary source
# os.environ['POLYGON_API_KEY'] = 'your_key_here'

print("=" * 80)
print("🧪 LEVEL 1: DIRECT TOOL TEST")
print("=" * 80)

# Test 1: Can we import it?
print("\nTest 1.1: Import test...")
try:
    from tools.top_companies import get_top_companies
    print("✅ Import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nTroubleshooting:")
    print("  - Is the file at tools/top_companies.py?")
    print("  - Are there any syntax errors?")
    print("  - Run: python -m py_compile tools/top_companies.py")
    sys.exit(1)

print("\n" + "=" * 80)

# Test 2: Can we call it with valid input?
print("\nTest 1.2: Simple execution test...")
print("Query: get_top_companies('technology', 3)")

try:
    result = get_top_companies('technology', 3)
    
    if result['success']:
        print("✅ Tool executed successfully")
        
        # Check structure
        data = result['data']
        required_fields = ['industry_query', 'sector', 'companies', 'total_in_sector']
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print(f"⚠️ Missing fields in data: {missing}")
        else:
            print("✅ All required fields present")
        
        # Show results
        print(f"\n   Industry: {data['industry_query']}")
        print(f"   Sector: {data['sector']}")
        print(f"   Data Source: {data.get('data_source_used', 'unknown')}")
        print(f"   Companies found: {data['total_in_sector']}")
        print(f"\n   Top 3:")
        
        for i, comp in enumerate(data['companies'][:3], 1):
            cap_b = comp['market_cap'] / 1e9
            print(f"   {i}. {comp['ticker']}: {comp['name']} (${cap_b:.1f}B)")
        
        print(f"\n   Confidence: {result['confidence']}")
        print(f"   Source: {result['source']}")
        
    else:
        print(f"⚠️ Tool returned error: {result['error']}")
        print("   (This might be OK if network/API is unavailable)")

except Exception as e:
    print(f"❌ Execution failed: {e}")
    import traceback
    traceback.print_exc()
    print("\nTroubleshooting:")
    print("  - Check the error traceback above")
    print("  - Are dependencies installed? (yfinance, requests, etc.)")
    print("  - Is .cache directory writable?")

print("\n" + "=" * 80)

# Test 3: Invalid industry
print("\nTest 1.3: Edge case - invalid industry...")
result = get_top_companies('invalid_industry_xyz', 5)

if not result['success']:
    print("✅ Correctly rejected invalid industry")
    print(f"   Error message: {result['error']}")
else:
    print("⚠️ Should have rejected invalid industry")

# Test 4: Different industries
print("\nTest 1.4: Multiple industries...")
test_industries = [
    ('healthcare', 5),
    ('finance', 3),
    ('energy', 2),
]

for industry, n in test_industries:
    print(f"\n  Testing: {industry} (top {n})")
    result = get_top_companies(industry, n)
    
    if result['success']:
        data = result['data']
        companies = data.get('companies', [])
        print(f"  ✅ Found {len(companies)} companies")
        if companies:
            print(f"     Top: {companies[0]['ticker']}")
        else:
            print("     Top: none")
    else:
        print(f"  ⚠️ Failed: {result['error']}")

print("\n" + "=" * 80)