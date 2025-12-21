'''
Nodes package - contains all LangGraph nodes

Each node is a function that:
1. Takes the current state
2. Does some work
3. Returns updates to the state

Nodes in this package:
- planner: Breaks down queries into tools calls
- exectutor: Runs the tools
- Validator: checks data quality (phase 3)
- reporter: Formats the final answer
'''

from nodes.planner import planner_node
from nodes.executor import executor_node
from nodes.reporter import reporter_node

__all__ = ["planner_node", "executor_node", "reporter_node"]

'''
## Explanation

### What's a System Prompt?

**Simple:** Instructions you give to the AI before it starts working.

**Analogy:** Like giving instructions to a new employee:
```
"You're a financial planner. When someone asks a question,
break it into steps. Use these 4 tools. Output JSON only."
```

### Why JSON Output?

**Simple:** Structured data is easier to work with than text.

**Bad (text):**

"First, get Apple's financials. Then get revenue."
'''