'''
Reporter node - agent writer

The reporter is like a journalist who takes all the raw data
and writes a clean article for the reader.

This node takes all the raw tool results and creates:
1. A human-readable answer for the user
2. An audit trail (full transparency about what happened)
3. Metrics (latency, confidence, retry count)

Think of it like a journalist who:
- Takes raw data from multiple sources
- Writes a clear article
- Cites all sources
- Provides context and caveats

Example Flow:
Input (tool_results): [
  {"tool": "sec_analyzer", "data": {"revenue": 94930000000}, "confidence": 1.0}
]

Output (answer):
"# Analysis Results

**Company:** Apple Inc.
**Revenue:** $94.93B (Q4 2024)
**Source:** SEC 10-Q Filing
**Confidence:** 100% 🟢"

Why we need this:
- Raw data isn't user-friendly (94930000000 vs "$94.93B")
- Need to cite sources (audit trail)
- Need to show confidence (data quality)
- Need to calculate metrics (latency, success rate)
'''

from typing import Dict, Any, List
from datetime import datetime

#Main reporter function
def reporter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    '''
    How it works:
    1. Takes all tool results from state
    2. Formats each result nicely
    3. Calculates overall metrics
    4. Creates the audit trail (for UI transparency)
    5. Returns the final answer
    
    Args:
        state: Current agent state (must contain 'tool_results')
        
    Returns:
        Updated state with:
        - answer: Formatted response for user
        - audit_trail: Complete execution trace
        - overall_confidence: Average confidence score
        - end_time: When execution completed
        - total_latency_ms: How long it took
    '''

    #Extract data from state
    query = state.get("query", "")
    tool_results = state.get("tool_results", [])
    execution_log = state.get("execution_log", [])
    plan = state.get("plan", [])
    start_time = state.get("start_time", None)

    