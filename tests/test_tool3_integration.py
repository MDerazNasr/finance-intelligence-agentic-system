"""
Test that executor routes to top_companies correctly
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ['SEC_API_USER_AGENT'] = 'Test test@example.com'
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY', 'test-key')

print("=" * 80)
print("🧪 LEVEL 2: EXECUTOR INTEGRATION TEST")
print("=" * 80)

# Test: Does executor route correctly?
print("\nTest 2.1: Executor routing...")

try:
    from agent.state import create_initial_state
    from nodes.executor import executor_node
    
    # Create a state with a plan that calls get_top_companies
    state = create_initial_state("Top 5 tech companies")
    state['plan'] = [{
        'tool_name': 'get_top_companies',
        'parameters': {'industry': 'technology', 'n': 5},
        'reason': 'Get top tech companies by market cap'
    }]
    
    print("   Running executor with plan:")
    print(f"   - Tool: {state['plan'][0]['tool_name']}")
    print(f"   - Params: {state['plan'][0]['parameters']}")
    
    # Execute
    updated_state = executor_node(state)
    
    # Check results
    tool_results = updated_state.get('tool_results', [])
    
    if tool_results:
        result = tool_results[0]
        print(f"\n✅ Executor routing successful")
        print(f"   Tool called: {result['tool_name']}")
        print(f"   Success: {result['success']}")
        print(f"   Confidence: {result.get('confidence', 0)}")
        
        if result['success']:
            data = result['data']
            print(f"   Companies returned: {len(data.get('companies', []))}")
            print(f"   Data source: {data.get('data_source_used', 'unknown')}")
        else:
            print(f"   Error: {result.get('error')}")
    else:
        print("❌ No tool results returned")
        print("   Check executor routing logic")

except Exception as e:
    print(f"❌ Integration test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)