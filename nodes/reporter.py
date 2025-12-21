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

    #Add to log
    execution_log.append("Reporter: Generating final report")

    #Build answer
    answer_parts = []

    answer_parts.append("\n No data was retrieved. Please try a different query. \n")
    answer_parts.append(f"Query:** {query}\n")

    #Check if we have any results
    if not tool_results:
        answer_parts.append("\n No data was retrieved. Please try a different query.\n")
        execution_log.append("No tool results to report")    
    else:
        execution_log.append(f"   📝 Formatting {len(tool_results)} result(s)")

    #Format each tool result
        for i, result in enumerate(tool_results, 1):
            answer_parts.append(f"\n---\n")
            answer_parts.append(f"\n## Result {i}: {result['tool_name']}")
            
            # Format based on whether it succeeded or failed
            if result["success"]:
                formatted = _format_successful_result(result)
                answer_parts.append(formatted)
            else:
                formatted = _format_failed_result(result)
                answer_parts.append(formatted)
    
    # Join all parts into final answer
    answer = "\n".join(answer_parts)

    #Calculate metrics

    #End time
    end_time = datetime.utcnow().isoformat()
    #Calc total latency
    total_latency_ms = 0.0
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            total_latency_ms = (end_dt - start_dt).total_seconds() * 1000
        except:
            #if datetime parsing fails, just use 0
            pass

    #Calculate overall confidence (average of all successful results)
    sucessful_results = []
    for r in tool_results:
        if r["success"]:
            sucessful_results.append(r)
    if sucessful_results:
        overall_confidence = sum(r["confidence"]) for r in sucessful_results / len(successful_results)
    else:
        overall_confidence = 0.0
    
    #Count successes and failures
    num_success = len(sucessful_results)
    num_failed = len(tool_results) - num_success

    execution_log.append(
        f"Report complete: {num_success} succeeded, {num_failed} failed"
    )
    execution_log.append(
        f"Overall confidence: {overall_confidence:.0%}"
    )
    execution_log.append(
        f"Total latency: {total_latency_ms:.0f}ms"
    )
    #Create audit trail
    #The audit trail is a complete record of everything that happened
    #This will be displayed in the UI to show transparency
    audit_trail = {
        "query": query,
        "plan": plan,
        "tool_results": tool_results,
        "execution_log": execution_log,
        "metrics": {
            "overall_confidence": overall_confidence,
            "num_tools_called": len(tool_results),
            "num_success": num_success,
            "num_failed": num_failed,
            "total_latency_ms": total_latency_ms,
            "retry_count": state.get("retry_count", 0)
        },
        "timestamps": {
            "start": start_time,
            "end": end_time
        }
    }

    #Return updated state
    return {
        "answer": answer,
        "audit_trail": audit_trail,
        "overall_confidence": overall_confidence,
        "end_time": end_time,
        "total_latency_ms": total_latency_ms,
        "execution_log": execution_log
    }

    }