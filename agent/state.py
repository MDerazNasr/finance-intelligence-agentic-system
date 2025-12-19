'''
Agent state - the agent's memory
This flows through: Planner -> Executor -> Validator -> Reporter
'''

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

'''
TypedDict is a typing construct that lets you define the expected shape of a 
dictionary, tells which keys exist and what types their valus should have witout
turning it into a class/changing runtime

TypedDict - Type hints help catch bugs
ToolResult has metadata - Every piece of data has provenance
execution_log - Makes debugging easy
confidence - We track data quality from the start
'''

class ToolCall(TypedDict):
    #A planned tool call
    tool_name: str
    parameters: Dict[str, Any]
    reason: str

class ToolResult(TypedDict):
    """Result from a tool with metadata"""
    tool_name: str
    parameters: Dict[str, Any]
    data: Any                # The actual data returned
    source: str              # Where it came from (SEC URL, API, etc)
    timestamp: str           # When it was fetched
    confidence: float        # 0.0 to 1.0 (XBRL=1.0, API=0.8, Web=0.5)
    success: bool
    error: Optional[str]

class AgentState(TypedDict):
    #The complete agent memory

    #input
    query:str

    #Planning
    plan: List[ToolCall]
    plan_reasoning: str

    #Execution
    tool_results: List[ToolResult]
    execution_log: List[str]

    #Validation (Phase 3)
    overall_confidence: float
    needs_retry: bool
    retry_count: int

    #Output
    answer: str
    audit_trail: Dict[str, Any]

    #Telemetry
    start_time: str
    total_latency_ms: Optional[float]

def create_initial_state(query: str) -> AgentState:
    #Create fresh state for a new query
    return AgentState(
        query=query,
        plan=[],
        plan_reasoning="",
        tool_results=[],
        execution_log=[],
        overall_confidence=0.0,
        needs_retry=False,
        retry_count=0,
        answer="",
        audit_trail={},
        start_time=datetime.utcnow().isoformat(),
        total_latency_ms=None
    )