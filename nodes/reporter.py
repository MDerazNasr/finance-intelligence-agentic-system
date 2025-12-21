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
        overall_confidence = sum(r["confidence"] for r in sucessful_results) / len(successful_results)
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

def _format_successful_result(result: Dict[str, Any]) -> str:
    '''
    Formats a successful tool result for display.

    This function knows how to format each type of tool's output
    It's like having different templates for different types of articles

    Args:
        result:  A ToolResult that succeeded
    Returns:
        Formatted string for display
    
    Example:
            Input: {"tool_name": "sec_analyzer", "data": {"revenue": 94930000000}}
            Output: "**Revenue:** $94.93B" 
    '''

    tool_name = result["tool_name"]
    data = result["data"]

    #Start with the confidence indicator
    confidence = result["confidence"]
    confidence_emoji = _get_confidence_emoji(confidence)

    output = []
    output.append(f"\n**Confidence:** {confidence:.0%} {confidence_emoji}")
    output.append(f"**Source:** {result['source']}")

    #Format based on tool type
    if tool_name == "get_quarterly_financials" and data:
        #Format SEC financial data
        output.append(f"\n**Company:** {data.get('company_name', 'Unknown')}")
        output.append(f"**Filing Date:** {data.get('filing_date', 'Unknown')}")
        output.append(f"**Period End:** {data.get('period_end', 'Unknown')}")
    
        #Format the financial metrics
        output.append(f"\n**Financial Metrics:**")
        financials = data.get("financials", {})

        if financials:
            for key, value in financials.items():
                label = value.get("label", key)
                amount = value.get("value", 0)
                #Format large numbers with commas and B/M suffixes
                formatted_amount = _format_currency(amount)
                output.append(f"- **{label}:** {formatted_amount}")
        else:
            output.append("- No financial metrics available")
        
        # Add filing URL
        filing_url = data.get("filing_url", "")
        if filing_url:
            output.append(f"\n[View SEC Filing]({filing_url})")

    elif tool_name == "find_competitors" and data:
        # Format competitor data (Phase 2)
        competitors = data.get("competitors", [])
        output.append(f"\n**Competitors Found:** {len(competitors)}")
        
        for comp in competitors[:5]:  # Show top 5
            ticker = comp.get("ticker", "")
            name = comp.get("name", "")
            output.append(f"- **{ticker}:** {name}")
    
    elif tool_name == "get_top_companies" and data:
        # Format top companies data (Phase 2)
        companies = data.get("companies", [])
        output.append(f"\n**Top {len(companies)} Companies:**")
        
        for i, comp in enumerate(companies, 1):
            ticker = comp.get("ticker", "")
            name = comp.get("name", "")
            market_cap = comp.get("market_cap", 0)
            formatted_cap = _format_currency(market_cap)
            output.append(f"{i}. **{ticker}** - {name} (Market Cap: {formatted_cap})")
    
    elif tool_name == "research_ai_disruption" and data:
        # Format AI disruption research (Phase 2)
        summary = data.get("summary", "")
        use_cases = data.get("use_cases", [])
        
        output.append(f"\n**AI Disruption Analysis:**")
        output.append(summary)
        
        if use_cases:
            output.append(f"\n**Key Use Cases:**")
            for uc in use_cases[:5]:
                output.append(f"- {uc}")
    
    elif tool_name == "general_financial_research" and data:
        # Format general research (Phase 2)
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        
        output.append(f"\n{answer}")
        
        if sources:
            output.append(f"\n**Sources:**")
            for src in sources[:3]:
                title = src.get("title", "")
                url = src.get("url", "")
                output.append(f"- [{title}]({url})")
    
    else:
        # Generic fallback for unknown tool types
        output.append(f"\n**Data:** {data}")
    
    return "\n".join(output)

def _format_failed_result(result: Dict[str, Any]) -> str:
    '''
    Formats a failed tool result for display.

    When a tool fails, we want to:
    1. Show it failed clearly
    2. Explain why (error message)
    3. Not crash the whole report

    Args:
        result: A ToolResult that failed
    Returns:
        Formatted error message
    '''
    output = []

    output.append(f"\n**Status:** Failed")
    output.append(f"**Error:** {result.get('error', 'Unknown error')}")

    #Add helpful context
    params = result.get("parameters, {}")
    if params:
        output.append(f"**Parameters:** {params}")
    
    #Suggest what to do
    output.append(f"\n *Tip: Try a different query of check the parameter values*")

    return "\n".join(output)

#Helper Functions
def _get_confidence_emoji(confidence: float) -> str:
    '''
    Returns an emoji based on confidence level.

    This is a visual indicator of data quality:
    - 🟢 High confidence (0.8-1.0): Official, audited data
    - 🟡 Medium confidence (0.5-0.8): Reliable but derived
    - 🟠 Low confidence (0.3-0.5): Best effort, might be outdated
    - 🔴 Very low confidence (0.0-0.3): Unreliable
    
    Args:
        confidence: Float between 0.0 and 1.0
        
    Returns:
        Emoji string    
    '''

    if confidence >= 0.8:
        return "🟢"  # Green - High confidence
    elif confidence >= 0.5:
        return "🟡"  # Yellow - Medium confidence
    elif confidence >= 0.3:
        return "🟠"  # Orange - Low confidence
    else:
        return "🔴"  # Red - Very low confidence
    
def _format_currency(amount: float) -> str:
    """
    Formats a number as currency with appropriate suffixes.
    
    This makes large numbers readable:
    - 94930000000 → "$94.93B"
    - 1500000000 → "$1.50B"
    - 25000000 → "$25.00M"
    - 500000 → "$500.00K"
    
    Args:
        amount: Dollar amount (raw number)
        
    Returns:
        Formatted string with B/M/K suffix
        
    Why this matters:
    - Professional terminals show "$94.93B" not "$94,930,000,000"
    - Easier to read and compare
    - Shows attention to UX detail
    """
    if abs(amount) >= 1_000_000_000:
        # Billions
        return f"${amount / 1_000_000_000:.2f}B"
    elif abs(amount) >= 1_000_000:
        # Millions
        return f"${amount / 1_000_000:.2f}M"
    elif abs(amount) >= 1_000:
        # Thousands
        return f"${amount / 1_000:.2f}K"
    else:
        # Just dollars
        return f"${amount:.2f}"

def _calculate_confidence_color(confidence: float) -> str:
    """
    Returns a color code for confidence (for future UI use).
    
    This will be used in the Streamlit UI to color-code confidence scores.
    
    Args:
        confidence: Float between 0.0 and 1.0
        
    Returns:
        Color name (for Streamlit)
    """
    if confidence >= 0.8:
        return "green"
    elif confidence >= 0.5:
        return "orange"
    else:
        return "red"