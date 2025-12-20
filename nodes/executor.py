"""
Executor Node - The Agent's "Hands"

This node takes the plan created by the Planner and actually executes it.

Think of it like a project coordinator who:
1. Reads the plan (list of tool calls)
2. Calls each tool one by one
3. Collects all the results
4. Logs what happened

Example Flow:
Plan: [
  {"tool_name": "sec_analyzer", "parameters": {"ticker": "AAPL"}},
  {"tool_name": "sec_analyzer", "parameters": {"ticker": "GOOGL"}}
]

Executor:
  Step 1: Call sec_analyzer("AAPL") → Success! Got revenue data
  Step 2: Call sec_analyzer("GOOGL") → Success! Got revenue data
  
Result: 2 ToolResults in the state

Why we need this:
- Separates planning from execution (single responsibility principle)
- Handles errors gracefully (if one tool fails, others still run)
- Logs everything for debugging
- Can add retry logic here later
"""
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
from typing import Dict, Any, List
from agent.state import ToolResult
from tools.sec_analyzer import get_latest_quarterly_financials

#main function
def executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    '''
    The executor node -> acutally runs the planned tool calls

    How it works:
    1. Reads the plan from the state (created the Planner)
    2. For each step in the plan:
        a. Figure out which tool to call
        b. Call it with the right parameters
        c. Collect the result
        d. Log what happened
    3. Return all results to the state

    Args:
        state: Current agent state (must contain 'plan')
    
    Returns:
        Uploaded state with:
        - tool_results: List of ToolResult objects
        - execution_log: Updated log with what happened
    
    Example:
        Input state: {
            "plan": [{"tool_name": "sec_analyzer", "parameters": {"ticker": "AAPL"}}],
            ...
        }
        
        Output: {
            "tool_results": [{
                "tool_name": "sec_analyzer",
                "data": {"revenue": 94930000000, ...},
                "confidence": 1.0,
                "success": True,
                ...
            }],
            "execution_log": ["🔧 Executing 1 tool calls", "Step 1/1: sec_analyzer...", ...]
        }    
    '''

    #extract plan and log from state
    plan = state.get("plan", [])
    execution_log = state.get("execution_log", [])
    tool_results = [] # We'll collect results here

    #Log that we're starting execution
    execution_log.append(f"Executor: Starting execution of {len(plan)} step(s)")

    # if no plan, we can't do anything
    if not plan:
        execution_log.append("No plan provided - nothing to execute")
        return {
            "tool_results": [],
            "execution_log": execution_log
        }
    
    #execute each step in the plan
    for i, step in enumerate(plan, 1):
        #extract info from this step
        tool_name = step.get("tool_name", "unknown")
        parameters = step.get("parameters", {})
        reason = step.get("reason", "No reason provided")

        #Log what we're about to do
        execution_log.append(
            f" Step {i}/{len(plan)}: {tool_name}({parameters})"
        )
        execution_log.append(f"Reason: {reason}")
        try:
            #route to the appropiate tool
            #this is like a switchboard operator connecting the right line
            result = _route_to_tool(tool_name, parameters, execution_log)

            #log the result
            if result["success"]:
                execution_log.append(
                    f"Success: (confidence: {result['confidence']:.0%})"
                )
            else:
                execution_log.append(
                    f"Failed: {result.get('error', 'Unknown error')}"
                )
            #Add result to our collection
            tool_results.append(result)
        
        except Exception as e:
            #Something went wrong
            execution_log.append(f"Exception: {str(e)}")
            # Create an error result
            error_result = ToolResult(
                tool_name=tool_name,
                parameters=parameters,
                data=None,
                source="executor",
                timestamp="",
                confidence=0.0,
                success=False,
                error=f"Executor exception: {str(e)}"
            )
            tool_results.append(error_result)

    # Summary
    successful = sum(1 for r in tool_results if r["success"])
    failed = len(tool_results) - successful
    
    execution_log.append(
        f"Execution complete: {successful} succeeded, {failed} failed"
    )
    # Return updated state
    return {
        "tool_results": tool_results,
        "execution_log": execution_log
    }

#tool routing function
def _route_to_tool(
        tool_name: str,
        parameters: Dict[str, Any],
        execution_log: List[str]
) -> ToolResult:
    '''
    Routes a tol call to the appropiate function.

    This is the "switchboard" that connects tool names to actual functions.

    How it works:
    - Input: tool_name="sec_analyzer", parameters={"ticker": "AAPL"}
    - Output: Calls get_latest_quarterly_financials("AAPL")
    - Returns: ToolResult from that function
    
    Why we need this:
    - The Planner only knows tool names (strings)
    - We need to map those strings to actual Python functions
    - Centralized place to add new tools (just add another elif)
    
    Args:
        tool_name: Name of the tool (from the plan)
        parameters: Dict of parameters for the tool
        execution_log: Log to append debug info
        
    Returns:
        ToolResult from the called tool
    '''

    #Tool 1 - SEC ANALYZER (XBRL Fiancial Data)
    if tool_name == "get_quarterly_financials":
        ticker = parameters.get("ticker", "")

        if not ticker:
            #Missing required parameter
            return ToolResult(
                tool_name=tool_name,
                parameters=parameters,
                data=None,
                source="executor",
                timestamp="",
                confidence=0.0,
                success=False,
                error="Missing required parameter: ticker"
            )
        # Call the actual tool
        return get_latest_quarterly_financials(ticker)
    
    #Tool 2 - Competitor Finder (Phase 2)
    elif tool_name == "find_competitors":
        #Placeholders until we build this in Phase 2
        execution_log.append("Tool not yet implemented: find_competitors")

        return ToolResult(
            tool_name=tool_name,
            parameters=parameters,
            data={"message": "Tool not yet implemented (Phase 2)"},
            source="placeholder",
            timestamp="",
            confidence=0.0,
            success=False,
            error="Tool not implemented yet - coming in Phase 2"
        )
    # Tool 3: Top Companies Ranker (Phase 2)
    elif tool_name == "get_top_companies":
        # Placeholder until we build this in Phase 2
        execution_log.append("Tool not yet implemented: get_top_companies")
        
        return ToolResult(
            tool_name=tool_name,
            parameters=parameters,
            data={"message": "Tool not yet implemented (Phase 2)"},
            source="placeholder",
            timestamp="",
            confidence=0.0,
            success=False,
            error="Tool not implemented yet - coming in Phase 2"
        )
    
    # Tool 4: AI Disruption Research (Phase 2)
    elif tool_name == "research_ai_disruption":
        # Placeholder until we build this in Phase 2
        execution_log.append("Tool not yet implemented: research_ai_disruption")
        
        return ToolResult(
            tool_name=tool_name,
            parameters=parameters,
            data={"message": "Tool not yet implemented (Phase 2)"},
            source="placeholder",
            timestamp="",
            confidence=0.0,
            success=False,
            error="Tool not implemented yet - coming in Phase 2"
        )
    
    # Tool 5: General Research (Fallback) (Phase 2)
    elif tool_name == "general_financial_research":
        # Placeholder until we build this in Phase 2
        execution_log.append("Tool not yet implemented: general_financial_research")
        
        return ToolResult(
            tool_name=tool_name,
            parameters=parameters,
            data={"message": "Tool not yet implemented (Phase 2)"},
            source="placeholder",
            timestamp="",
            confidence=0.0,
            success=False,
            error="Tool not implemented yet - coming in Phase 2"
        )
    
    # Unknown Tool (Error Case)
    else:
        execution_log.append(f"Unknown tool: {tool_name}")
        return ToolResult(
            tool_name=tool_name,
            parameters=parameters,
            data=None,
            source="executor",
            timestamp="",
            confidence=0.0,
            success=False,
            error=f"Unknown tool: {tool_name}. Available tools: get_quarterly_financials, find_competitors, get_top_companies, research_ai_disruption, general_financial_research"
        )
    
#Helper function - Validate Parameters
def _validate_parameters(tool_name: str, parameters: Dict[str, Any]) -> tuple:
    '''
    Validates that required parameters are present for a tool.

    This prevents errors like calling sec_analyzer without a ticker.

    Args:
        tool_name: the tool being called
        parameters: the parameters provided

    Returns:
        (is_valid: bool, error_message: str or None)
    
Example:
    _validate_parameters("get_quarterly_financials", {})
    → (False, "Missing required parameter: ticker")
    
    _validate_parameters("get_quarterly_financials", {"ticker": "AAPL"})
    → (True, None)        
        '''
    # Define required parameters for each tool
    required_params = {
        "get_quarterly_financials": ["ticker"],
        "find_competitors": ["ticker"],
        "get_top_companies": ["industry", "n"],
        "research_ai_disruption": ["industry"],
        "general_financial_research": ["query"]
    }

    #Get required params for this tool
    required = required_params.get(tool_name, [])

    #Check each required param
    for param in required:
        if param not in parameters[param]:
            return False, f"Missing required parameter: {param}"
    
    return True, None

'''
whats happening simply:
1. planner (chef) - creates the recipe
2. executor (Line Cook) - actually cooks each dish
3. tools (kitchen stattion) - diffrent stations (grill, fryer)
'''