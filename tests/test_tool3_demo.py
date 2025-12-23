"""
Demo preparation: Test all demo queries and check consistency
"""

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ['SEC_API_USER_AGENT'] = 'Test test@example.com'

print("=" * 80)
print("🧪 LEVEL 4: DEMO PREPARATION TEST")
print("=" * 80)

from tools.top_companies import get_top_companies

# Demo queries you'll actually use
demo_queries = [
    ('technology', 5, "Top 5 tech companies"),
    ('healthcare', 10, "Top 10 healthcare companies"),
    ('finance', 5, "Top 5 financial companies"),
]

print("\n📊 Testing demo queries for consistency...\n")

timings = []

for industry, n, description in demo_queries:
    print(f"Testing: {description}")
    
    # Run twice to check caching
    start = time.time()
    result1 = get_top_companies(industry, n)
    time1 = time.time() - start
    
    start = time.time()
    result2 = get_top_companies(industry, n)
    time2 = time.time() - start
    
    timings.append((description, time1, time2))
    
    if result1['success']:
        data = result1['data']
        print(f"  ✅ Success")
        print(f"  Source: {data.get('data_source_used', 'unknown')}")
        print(f"  First run: {time1:.2f}s")
        print(f"  Second run (cached): {time2:.2f}s")
        print(f"  Top company: {data['companies'][0]['ticker']}")
    else:
        print(f"  ❌ Failed: {result1['error']}")
    
    print()

# Check consistency
print("=" * 80)
print("📈 TIMING ANALYSIS")
print("=" * 80)

for desc, t1, t2 in timings:
    delta = abs(t1 - t2)
    if delta < 0.3:
        status = "✅ Consistent"
    elif delta < 1.0:
        status = "⚠️ Acceptable"
    else:
        status = "❌ Inconsistent"
    
    print(f"{status} - {desc}")
    print(f"  First: {t1:.2f}s, Cached: {t2:.2f}s, Δ: {delta:.2f}s")

print("\n💡 Demo Tips:")
if max(t2 for _, _, t2 in timings) < 1.0:
    print("  ✅ All cached queries < 1s - demo will feel snappy!")
else:
    print("  ⚠️ Some queries > 1s - consider pre-caching more data")

if max(abs(t1 - t2) for _, t1, t2 in timings) < 0.5:
    print("  ✅ Consistent timing - won't look suspicious")
else:
    print("  ⚠️ Inconsistent timing - may need minimum delay adjustment")

print("\n" + "=" * 80)