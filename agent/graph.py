'''
LangGraph Workdlow - The agents assembly line

this file defines how the agent flows from start to finish:
1. user asks a question
2. planner creates a plan
3. exectuor runs the tools
4. reporter formats the answer
5. user gets the result

Why LangGraph?
- Makes the flow explicit (you can visualize it)
- Handles state management (passing data between nodes)
- Allows complex routing (we'll add validation loops in Phase 3)
- Industry standard for production agentic systems
'''

from typing import Literal
from langgraph.graph import StateGraph, END
from agent.state import AgentState, create_initial_state
from nodes.planner import planner_node
from nodes.executor import executor_node
from nodes.reporter import reporter_node

#Graph construction
def create_agent_graph():
    '''
    Creates and compiles the agent's state machine.

    How it works:
    1. Create a StateGraph with our AgentState schema
    2. Add nodes (the stations in the assembly line)
    3. Defines edges (how work flows between stations)
    4. Compiles into an executable graph
    
    Returns:
        Compiled LangGraph that can be invoked with inital state

    Example usage:
        graph = create_agent_graph()
        result = graph.invoke({"query": "What was Apple's revenue?"})
        print(result["answer"])
    
    Why this design?
    - Explicit flow (easy to understand and debug)
    - Type-safe state (AgentState schema enforces structure)
    - Extensible (easy to add validation node in Phase 3)
    - Testable (can test each node independently)
    '''

    #Step 1 - Create the state graph
    #This tells LangGraph what type of state to use
    #AgentState is our TypedDict with all the fields (query, plan, results, etc.)
    workflow = StateGraph(AgentState)

    #Step 2: Add notes to the graph
    #Each node is a function that takes state and returns updates
    #Think of these as stations on an assembly line

    workflow.add_node(
        "planner", #Name of this node (for routing)
        planner_node #The actual function to call
    )
    # What it does: Takes query, returns plan
    # Example: {"query": "..."} → {"plan": [...], "plan_reasoning": "..."}

    workflow.add_node(
        "executor",
        executor_node
    )
    # What it does: Takes plan, returns tool results
    # Example: {"plan": [...]} → {"tool_results": [...], "execution_log": [...]}
    
    workflow.add_node(
        "reporter",
        reporter_node
    )
    # What it does: Takes tool results, returns formatted answer
    # Example: {"tool_results": [...]} → {"answer": "...", "audit_trail": {...}}

    #Step 3 - Define the flow (edges between nodes)
    # Set the entry point (Where the graph starts)
    workflow.set_entry_point("planner") # These are like conveyor belts connecting the stations/ defines the edges (how data flows)

    workflow.add_edge(
        "planner",
        "executor"
    )
    workflow.add_edge(
        "executor",
        "reporter"
    )
    workflow.add_edge(
        "reporter",
        END
    )

    #Step 4 - compiling the graph
    '''
    # Compilation validates the graph and creates an executable version
    # This catches errors like:
    # - Nodes that aren't connected
    # - Cycles that would loop forever
    # - Missing entry points
    '''
    compiled_graph = workflow.compile()
    return compiled_graph

#Helper function - run graph with query
def run_agent(query: str) -> dict:
    """
    Convenience function to run the agent with a simple query string.
    
    This wraps the graph invocation to make it easier to use.
    Instead of creating the initial state manually, you just pass a query.
    
    Args:
        query: The user's question (e.g., "What was Apple's revenue?")
        
    Returns:
        The final state after the graph completes
        Contains: answer, audit_trail, confidence, etc.
        
    Example:
        result = run_agent("What was Apple's revenue?")
        print(result["answer"])
        print(result["overall_confidence"])
        
    Why this is useful:
    - Simpler API for common use case
    - Handles state initialization
    - Good for testing and demos
    """
    graph = create_agent_graph()
    #Create initial state from query
    initial_state = create_initial_state(query)

    #Run the graph
    final_state = graph.invoke(initial_state)
    return final_state

#for vizualization
def get_graph_visualization():
    """
    Returns a string representation of the graph structure.
    
    This is useful for:
    - Debugging (see how nodes are connected)
    - Documentation (show the flow in README)
    - Interviews (draw it on screen)
    
    Returns:
        ASCII art representation of the graph
        
    Example output:
        START → planner → executor → reporter → END
    """
    return """
    Agent Workflow (Phase 1):
    
    ┌─────────┐
    │  START  │
    └────┬────┘
         │
         ▼
    ┌─────────────┐
    │   PLANNER   │  ← Uses LLM to decompose query
    │             │    into tool calls
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │  EXECUTOR   │  ← Runs each tool and collects
    │             │    results with metadata
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │  REPORTER   │  ← Formats results into clean
    │             │    answer with audit trail
    └──────┬──────┘
           │
           ▼
    ┌─────────┐
    │   END   │
    └─────────┘
    
    State Flow:
    1. Input:  {"query": "What was Apple's revenue?"}
    2. Planner adds: {"plan": [...], "plan_reasoning": "..."}
    3. Executor adds: {"tool_results": [...], "execution_log": [...]}
    4. Reporter adds: {"answer": "...", "audit_trail": {...}}
    5. Output: Complete state with all fields populated
    """



