# In nodes/planner.py

'''
Planner Node - The agents Brain
The planner is like the project manager, for every query
1. Get top 5 healthcare companies - use get_top_companies tool
2. For each company, get their revenue (use sec_analyzer tool 5 times)

It uses Gemini to think through the query and create a plan in JSON
format

This node takes the users question and figures out:
1. what tools we need
2. in what order?
3. with what parameters?

Think of it like a project manager breaking down a big task into steps.

Example - 
User - "What was apples revenues last quarter?
Planner - [{"tool": "sec_analyzer", "params": {"ticker": "AAPL"}}]

User - Top 5 healthcare companies and their revenues
Planner: [
  {"tool": "get_top_companies", "params": {"industry": "healthcare", "n": 5}},
  {"tool": "sec_analyzer", "params": {"ticker": "UNH"}},
  {"tool": "sec_analyzer", "params": {"ticker": "JNJ"}},
  ...
]
'''

import os
import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

#Step 1 - Initialise the LLM (Gemini)
def get_llm():
    """
    Creates a connection to Gemini 3 Flash.
    
    Why Gemini 3 Flash (Released Dec 17, 2025)?
    - 78% on SWE-bench Verified (best for agentic coding)
    - 3x faster than Gemini 2.5 Pro
    - Outperforms larger models at fraction of cost
    - Optimized for multi-step tool orchestration
    - Excellent JSON structure output
    
    Alternative considerations:
    - GPT-5: Slightly better raw reasoning but 3x more expensive
    - Claude 3.5 Sonnet: Best instruction following but slower
    
    For financial data extraction with multi-tool workflows,
    Gemini 3 Flash offers the best speed/quality/cost balance.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment. "
            "Get one at: https://aistudio.google.com/apikey"
        )
    
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash",  # Latest model (Dec 17, 2025)
        temperature=0,            # Deterministic for planning
        google_api_key=api_key
    )

#Define the system prompt (instructions for gemini)
PLANNER_SYSTEM_PROMPT = """You are a financial analysis planning expert. Your ONLY job is to create a plan.

AVAILABLE TOOLS:

1. get_quarterly_financials(ticker: str)
    Purpose - Extract financial data from a company's latest 10-Q SEC filing
    Returns - revenue, net_income, operating_expenses, cost_of_revenue
    Example - get_quarterly_financials("AAPL")
    When to use: user asks abotu financials, revenue, income, profits, costs

2. find_competitors(ticker: str)
    Purpose - Find the main competitors for a company
    Returns - List of competitor tickers with company names
    Example - find_competitors("TSLA")
    When to use - User asks about competitors, peers, rivals

3. get_top_companies(industry: str, n: int)
   Purpose: Get top N companies in an industry ranked by market cap
   Returns: ranked list with tickers, names, market caps
   Example: get_top_companies("healthcare", 5)
   When to use: User asks for top/largest/biggest companies in a sector

4. research_ai_disruption(industry: str)
   Purpose: Research how AI is disrupting an industry
   Returns: AI use cases, disruption analysis, examples
   Example: research_ai_disruption("finance")
   When to use: User asks about AI impact, disruption, use cases

YOUR TASK:
    1. Read the user's question
    2. Figure out which tools to call and in what order
    3. Output ONLY valid JSON (no markdown, no explanation, no preamble)

OUTPUT FORMAT:
{
    "reasoning": "Brief explanation of your approach",
    "steps": [
        {
            "tool_name": "name_of_tool",
            "parameters": {"param": "value"},
            "reason": "Why this step is needed"
        }
    ]
}

RULES:
- if user asks about multiple companies, create seperate steps for each
- Preserve logical order (e.g., get_top_companies BEFORE getting financials)
- Be specific with parameters (use extact ticker symbols when mentioned)
- Only use tools that are necessary
- If query is ambiguous, make reasonable assumptions

EXAMPLES:


User: "What was Google's revenue last quarter?"
Output:
{
  "reasoning": "User wants quarterly revenue for Google (GOOGL ticker)",
  "steps": [
    {
      "tool_name": "get_quarterly_financials",
      "parameters": {"ticker": "GOOGL"},
      "reason": "Extract revenue from latest 10-Q"
    }
  ]
}

User: "Top 3 tech companies and their revenues"
Output:
{
  "reasoning": "Need to first get top 3 tech companies, then get each one's revenue",
  "steps": [
    {
      "tool_name": "get_top_companies",
      "parameters": {"industry": "technology", "n": 3},
      "reason": "Get the top 3 tech companies by market cap"
    },
    {
      "tool_name": "get_quarterly_financials",
      "parameters": {"ticker": "AAPL"},
      "reason": "Get Apple's revenue (likely #1)"
    },
    {
      "tool_name": "get_quarterly_financials",
      "parameters": {"ticker": "MSFT"},
      "reason": "Get Microsoft's revenue (likely #2)"
    },
    {
      "tool_name": "get_quarterly_financials",
      "parameters": {"ticker": "GOOGL"},
      "reason": "Get Google's revenue (likely #3)"
    }
  ]
}

Remember: Output ONLY the JSON, nothing else!
"""

#step 3 - The main planner function
def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    '''
    The Planner Node - Creates a step by step plan for answering the query

    How it works:
        1. takes the user's query from state
        2. sends it to LLM with instructions
        3. Gemini returns a JSON plan
        4. We parse the plan and update the state

    Args:
        state: the current agent state (which contains the users query)

    Returns:
        Updated state with:
        - plan: List of tool calls to execute
        - plan_reasoning: Why this plan was chosen
        - execution_log: Human-readable lof of what happened

    Example flow:
        Input state: {"query": "What was Apple's revenue?", ...}
        Output: {"plan": [{"tool_name": "sec_analyzer", ...}], ...}
    '''

    #extract query
    query = state["query"]

    #get execution log/ create empty list if first time
    execution_log = state.get("execution_log", [])
    execution_log.append(f"Planner: Analyzing query: '{query}'")

    #Call gemini to create the plan
    try:
        #get the LLLM
        llm = get_llm()

        # Create the messages for Gemini
        # SystemMessage = instructions (the PLANNER_SYSTEM_PROMPT)
        # HumanMessage = the actual user query
        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=f"User Query: {query}\n\nCreate a plan:")
        ]

        execution_log.append("Sending query to Gemini for planning....")
        #Invoke LLM to make API call
        response = llm.invoke(messages)
        #extract text from response
        response_text = response.content.strip()

        #Parse the JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            # Extract JSON from between ``` and ```
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        #Parse the JSON
        plan_data = json.loads(response_text)
        #extract the plan steps and reasoning
        plan = plan_data.get("steps", [])
        reasoning = plan_data.get("reasoning", "No reasoning provided")

        execution_log.append(f"Plan Created: {len(plan)} step(s)")
        execution_log.append(f"Reasoning: {reasoning}")

        #Log each step
        for i, step in enumerate(plan, 1):
            tool_name = step.get("tool_name", "unknown")
            params = step.get("parameters", {})
            reason = step.get("reason", "")
            execution_log.append(
                f"Step {i}: {tool_name}({params}) - {reason}"
            )
        #Reason the updated state
        return {
            "plan": plan, #The list of tool calls
            "plan_reasoning": reasoning, #Why this plan
            "execution_log": execution_log #Updated log
        }
    
    except json.JSONDecodeError as e:
        #JSON parsing failed - Gemini didn't return valid JSON
        execution_log.append(f"Failed to parse plan: Invalid JSON from LLM")
        execution_log.append(f"Error: {str(e)}")
        execution_log.append(f"Response was: {response_text[:200]}")

        #Create a fallback plan
        fallback_plan = _create_fallback_plan(query)
        execution_log.append(f"Using fallback plan: {len(fallback_plan)} step(s)")

        return {
            "plan": fallback_plan,
            "plan_reasoning": f"Fallback plan (LLM returned invalid JSON): {str(e)}",
            "execution_log": execution_log
        }
    
    except Exception as e:
        # Some other error occurred 
        execution_log.append(f"Planning failed with error: {str(e)}")

        #Create a fallback plan
        fallback_plan = _create_fallback_plan(query)
        execution_log.append(f"Using fallback plan: {len(fallback_plan)} step(s)")

        return {
            "plan": fallback_plan,
            "plan_reasoning": f"Fallback plan due to error: {str(e)}",
            "execution_log": execution_log
        }
    


