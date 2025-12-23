"""
End-to-end test: Full agent workflow with top_companies
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ['SEC_API_USER_AGENT'] = 'Test test@example.com'
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', 'your_actual_key_here')

print("=" * 80)
print("🧪 LEVEL 3: END-TO-END WORKFLOW TEST")
print("=" * 80)

# Test queries
test_queries = [
    "What are the top 5 technology companies?",
    "Show me the top 3 healthcare companies by market cap",
    "Top 10 financial services companies",
]

try:
    from agent.graph import run_agent
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test 3.{i}: {query}")
        print(f"{'='*80}")
        
        result = run_agent(query)
        
        # Check if it worked
        if result.get('overall_confidence', 0) > 0:
            print("✅ Query completed successfully")
            
            # Show plan
            plan = result.get('plan', [])
            print(f"\n📋 Plan ({len(plan)} steps):")
            for j, step in enumerate(plan, 1):
                print(f"   {j}. {step['tool_name']}({step.get('parameters', {})})")
            
            # Show results
            tool_results = result.get('tool_results', [])
            print(f"\n📊 Results ({len(tool_results)} tools executed):")
            for tr in tool_results:
                if tr['success']:
                    print(f"   ✅ {tr['tool_name']}: {tr.get('confidence', 0):.0%} confidence")
                else:
                    print(f"   ❌ {tr['tool_name']}: {tr.get('error', 'unknown')}")
            
            # Show answer preview
            answer = result.get('answer', '')
            print(f"\n💬 Answer preview:")
            print(answer[:500] + "..." if len(answer) > 500 else answer)
            
        else:
            print("❌ Query failed")
            print(f"Error: {result.get('error', 'Unknown')}")
        
        print()

except Exception as e:
    print(f"❌ E2E test failed: {e}")
    import traceback
    traceback.print_exc()

print("=" * 80)