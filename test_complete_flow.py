# test_complete_flow.py
"""
Complete Flow Test - Phase 1 Validation

This script tests the entire agent workflow end-to-end:
1. Load environment
2. Create the graph
3. Run test queries
4. Validate results

Run this to make sure everything works before Phase 2.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for required API keys
required_keys = {
    "GOOGLE_API_KEY": "https://aistudio.google.com/apikey",
    "SEC_API_USER_AGENT": "MohamedNasr mderaznasr@gmail.com"
}

missing_keys = []
for key, help_url in required_keys.items():
    if not os.getenv(key):
        missing_keys.append(f"  - {key} (get from: {help_url})")

if missing_keys:
    print("❌ ERROR: Missing required environment variables:")
    print("\n".join(missing_keys))
    print("\nPlease add them to your .env file")
    sys.exit(1)

print("✓ Environment variables loaded\n")

# Import after env is loaded
from agent.graph import run_agent

# ==============================================================================
# TEST QUERIES
# ==============================================================================

test_queries = [
    {
        "query": "What was Apple's revenue in their latest quarterly report?",
        "expected": "Should return XBRL data with ~$95B revenue for Q4 2024",
        "complexity": "Simple"
    },
    {
        "query": "What was Google's net income last quarter?",
        "expected": "Should return XBRL data with ~$26B net income for Q3 2024",
        "complexity": "Simple"
    },
    {
        "query": "Show me Microsoft's quarterly financials",
        "expected": "Should return revenue and net income from latest 10-Q",
        "complexity": "Simple"
    }
]

# ==============================================================================
# RUN TESTS
# ==============================================================================

print("=" * 80)
print("🧪 PHASE 1 - COMPLETE FLOW TEST")
print("=" * 80)
print(f"\nTesting {len(test_queries)} queries...\n")

results = []

for i, test in enumerate(test_queries, 1):
    print("=" * 80)
    print(f"TEST {i}/{len(test_queries)} [{test['complexity']}]")
    print("=" * 80)
    print(f"Query: {test['query']}")
    print(f"Expected: {test['expected']}\n")
    
    try:
        # Run the agent
        result = run_agent(test['query'])
        
        # Check if it succeeded
        success = result.get('overall_confidence', 0) > 0
        
        if success:
            print("✅ TEST PASSED")
            
            # Print key metrics
            print(f"\n📊 Metrics:")
            print(f"  - Confidence: {result.get('overall_confidence', 0):.0%}")
            print(f"  - Latency: {result.get('total_latency_ms', 0):.0f}ms")
            print(f"  - Tools Called: {len(result.get('tool_results', []))}")
            
            # Print answer preview - show key financial data
            answer = result.get('answer', '')
            print(f"\n📝 Answer Preview:")
            
            # Try to extract and show financial metrics if available
            tool_results = result.get('tool_results', [])
            if tool_results and tool_results[0].get('success') and tool_results[0].get('data'):
                data = tool_results[0]['data']
                if 'financials' in data:
                    print(f"  Company: {data.get('company_name', 'N/A')}")
                    print(f"  Filing Date: {data.get('filing_date', 'N/A')}")
                    print(f"  Financial Metrics:")
                    for key, value in data.get('financials', {}).items():
                        label = value.get('label', key)
                        amount = value.get('value', 0)
                        # Format amount
                        if abs(amount) >= 1_000_000_000:
                            formatted = f"${amount / 1_000_000_000:.2f}B"
                        elif abs(amount) >= 1_000_000:
                            formatted = f"${amount / 1_000_000:.2f}M"
                        else:
                            formatted = f"${amount:,.0f}"
                        print(f"    - {label}: {formatted}")
                else:
                    # Fallback to text preview
                    preview = answer[:400].replace('\n', ' ')
                    print(f"  {preview}...")
            else:
                # Show text preview
                preview = answer[:400].replace('\n', ' ')
                print(f"  {preview}...")
            
            results.append(("PASS", test['query']))
        else:
            print("❌ TEST FAILED - No data retrieved")
            results.append(("FAIL", test['query']))
            
    except Exception as e:
        print(f"❌ TEST FAILED - Exception: {str(e)}")
        results.append(("ERROR", test['query']))
        
        # Print traceback for debugging
        import traceback
        print("\nTraceback:")
        traceback.print_exc()
    
    print("\n")

# ==============================================================================
# SUMMARY
# ==============================================================================

print("=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)

passed = sum(1 for status, _ in results if status == "PASS")
failed = sum(1 for status, _ in results if status == "FAIL")
errors = sum(1 for status, _ in results if status == "ERROR")

print(f"\nResults: {passed} passed, {failed} failed, {errors} errors\n")

for status, query in results:
    emoji = "✅" if status == "PASS" else "❌"
    print(f"{emoji} [{status}] {query}")

print("\n" + "=" * 80)

if passed == len(test_queries):
    print("🎉 ALL TESTS PASSED - PHASE 1 COMPLETE!")
    print("=" * 80)
    print("\n✨ Ready for Phase 2: Implement remaining tools")
    print("   - competitor_finder")
    print("   - top_companies")
    print("   - ai_disruption")
    print("   - general_research\n")
else:
    print("⚠️  SOME TESTS FAILED")
    print("=" * 80)
    print("\nDebug steps:")
    print("1. Check .env file has correct API keys")
    print("2. Verify internet connection")
    print("3. Check error messages above")
    print("4. Try running individual tools manually\n")
'''
---

## 🎯 Explanation Time!

### What is a StateGraph?

**Simple:** A StateGraph is a flowchart where each box is a function that updates shared state.

**Analogy - Assembly Line:**
```
Station 1 (Planner):
  Input: Raw materials (query)
  Work: Design blueprint (plan)
  Output: Updated materials + blueprint

Station 2 (Executor):
  Input: Materials + blueprint
  Work: Build parts (run tools)
  Output: Materials + blueprint + parts

Station 3 (Reporter):
  Input: Materials + blueprint + parts
  Work: Package product (format answer)
  Output: Finished product

'''