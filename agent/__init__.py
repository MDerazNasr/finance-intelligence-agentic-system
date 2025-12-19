import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from agent.state import AgentState, ToolResult, create_initial_state

__all__ = ["AgentState", "ToolResult", "create_initial_state"]

#exposing API for agent package, to hide internal structure and making
#refactoring easier