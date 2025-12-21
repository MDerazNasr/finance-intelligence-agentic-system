"""
Agent Package - The Core Intelligence System

This package contains:
- state.py: The agent's memory schema (AgentState)
- graph.py: The workflow that orchestrates everything

Key exports:
- AgentState: Type definition for the agent's state
- create_initial_state: Factory for creating fresh state
- create_agent_graph: Main function to create the workflow
- run_agent: Convenience function to run queries
"""

import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.state import AgentState, ToolResult, create_initial_state
from agent.graph import create_agent_graph, run_agent

__all__ = [
    "AgentState", 
    "ToolResult", 
    "create_initial_state",
    "create_agent_graph",
    "run_agent"
]

#exposing API for agent package, to hide internal structure and making
#refactoring easier