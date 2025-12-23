# Sagard Analyst Sentinel - System Architecture

**Project:** AI-powered financial analyst agent  
**Interview:** Sagard AI Enablement Internship  
**Date:** Tuesday, 6pm  
**Core Philosophy:** Reliability-first, production-grade, demonstrable value

---

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Key Innovations](#key-innovations)

---

## High-Level Overview

### What It Does
An agentic system that answers financial analyst queries by:
- Breaking queries into structured tool calls (Planning)
- Executing tools with multiple data sources (Execution)
- Formatting professional reports (Reporting)
- Tracking data provenance and quality (Audit Trail)

### Core Capabilities
1. ✅ **SEC Financial Analysis** - Extract XBRL data from 10-Q filings (Confidence: 1.0)
2. ✅ **Competitor Discovery** - Find industry peers with cascading data sources (Confidence: 0.8-0.85)
3. 🚧 **Market Rankings** - Top N companies by market cap (Phase 2)
4. 🚧 **AI Disruption Research** - Industry AI trends (Phase 2)
5. 🚧 **General Research** - Fallback web search tool (Phase 2)

### Design Principles
- **Reliability First** - Cascading data sources, aggressive caching, fallbacks
- **Data Quality** - Confidence scoring, source tracking, validation
- **Transparency** - Complete audit trails, execution logs
- **Production-Grade** - Type-safe state, error handling, observability

---

## Architecture Diagram
```
                         ┌─────────────────────────────────────┐
                         │         USER QUERY                  │
                         │  "Find Tesla's competitors and      │
                         │   compare their revenues"           │
                         └──────────────┬──────────────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────────────┐
                         │      CREATE INITIAL STATE           │
                         │  AgentState: {query, plan: [],      │
                         │   tool_results: [], ...}            │
                         └──────────────┬──────────────────────┘
                                        │
                         ┌──────────────▼──────────────────────┐
                         │                                      │
                         │        LANGGRAPH WORKFLOW            │
                         │     (State Machine Orchestration)    │
                         │                                      │
                         └──────────────┬──────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│   PLANNER    │              │   EXECUTOR   │              │   REPORTER   │
│              │              │              │              │              │
│ LLM: Gemini  │              │ Tool Router  │              │ Formatter    │
│ 2.0 Flash    │──────────────▶ + Caller     │──────────────▶ + Metrics   │
│              │  plan: [     │              │ tool_results │              │
│ Input:       │   {tool,     │ Input:       │   [{data,    │ Input:       │
│ - query      │    params,   │ - plan       │     source,  │ - tool_results│
│              │    reason}]  │              │     conf}]   │              │
│ Output:      │              │ Output:      │              │ Output:      │
│ - plan       │              │ - tool_      │              │ - answer     │
│ - reasoning  │              │   results    │              │ - audit_     │
│              │              │ - exec_log   │              │   trail      │
└──────────────┘              └──────┬───────┘              └──────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │ SEC ANALYZER │ │ COMPETITOR   │ │ OTHER TOOLS  │
            │              │ │ FINDER       │ │ (Phase 2)    │
            │ Data Source: │ │              │ │              │
            │ - XBRL       │ │ Data Sources:│ │              │
            │ (edgartools) │ │ - Polygon.io │ │              │
            │              │ │ - yfinance ← │ │              │
            │ Confidence:  │ │              │ │              │
            │ 1.0          │ │ Confidence:  │ │              │
            │              │ │ 0.85/0.8     │ │              │
            └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Core Components

### 1. State Management (`agent/state.py`)

**Purpose:** The agent's "memory" - shared state flowing through all nodes

**Key Types:**
```python
AgentState = {
    query: str                    # User input
    plan: List[ToolCall]         # What to execute
    tool_results: List[ToolResult]  # Execution results
    execution_log: List[str]     # Human-readable trace
    overall_confidence: float    # Data quality score
    audit_trail: Dict           # Complete transparency
    ...
}

ToolResult = {
    tool_name: str
    data: Any                    # Actual results
    source: str                  # Data provenance
    confidence: float            # 0.0-1.0 quality score
    success: bool
    ...
}
```

**Why TypedDict?**
- Type hints catch bugs at development time
- Clear contract between nodes
- Self-documenting code

**Interview Talking Point:**
> "I use TypedDict for the agent state because it gives us compile-time type safety without the overhead of full classes. Each node knows exactly what fields exist and what types they are. This prevents runtime errors like missing keys or type mismatches."

---

### 2. Planning Node (`nodes/planner.py`)

**Purpose:** Query decomposition using LLM

**How It Works:**
1. Receives user query
2. Sends to Gemini 2.0 Flash with system prompt describing available tools
3. LLM returns JSON plan with reasoning
4. Parses plan into structured ToolCall objects
5. Has fallback logic if LLM fails (regex keyword matching)

**LLM Choice: Gemini 2.0 Flash**
- Released Dec 17, 2025 - Cutting edge
- 78% on SWE-bench Verified (best for agentic tasks)
- 3x faster than Gemini 2.5 Pro
- Excellent JSON structure output
- Cost-effective ($0.001/1K tokens)

**System Prompt Design:**
- Lists 5 available tools with signatures
- Provides decision tree logic
- Includes examples (few-shot learning)
- Enforces JSON-only output (no markdown)

**Fallback Strategy:**
If LLM fails (network, JSON parsing, API error):
- Use regex to detect ticker symbols (uppercase 1-5 chars)
- Match financial keywords (revenue, income, profit)
- Create simple plan: get_quarterly_financials(detected_ticker)
- Graceful degradation vs. total failure

**Interview Talking Point:**
> "The planner uses Gemini 2.0 Flash because it's optimized for multi-step tool orchestration. I include a fallback mechanism that uses keyword matching - if the LLM is unavailable, the agent still tries to answer using pattern matching. This is defensive programming - plan for failure."

---

### 3. Executor Node (`nodes/executor.py`)

**Purpose:** Tool routing and execution

**How It Works:**
1. Reads plan from state
2. For each step:
   - Routes tool_name string to actual Python function
   - Validates parameters
   - Calls tool with error handling
   - Collects ToolResult
3. Isolated error handling - one tool failure doesn't crash others
4. Returns all results (successes and failures)

**Tool Routing Pattern:**
```python
if tool_name == "get_quarterly_financials":
    return get_latest_quarterly_financials(ticker)
elif tool_name == "find_competitors":
    return find_competitors(ticker, limit)
# ... more tools
```

**Why This Design?**
- Centralized routing (one place to add tools)
- Type-safe dispatch
- Easy to test tools independently
- Clear contract (ToolResult interface)

**Interview Talking Point:**
> "The executor implements the strategy pattern - it routes string tool names to actual functions. This decouples the planner (which only knows tool names) from the implementation. Adding a new tool is just adding an elif clause. Each tool returns a standardized ToolResult, so the reporter doesn't need to know which tool ran."

---

### 4. Reporter Node (`nodes/reporter.py`)

**Purpose:** Format results into professional output

**How It Works:**
1. Takes tool results
2. Formats each based on tool type and success/failure
3. Calculates metrics (confidence, latency, success rate)
4. Creates complete audit trail
5. Returns formatted answer + metadata

**Formatting Features:**
- Currency formatting: `$94,930,000,000` → `$94.93B`
- Confidence indicators: 🟢 (high) 🟡 (medium) 🔴 (low)
- Source citations: Links to SEC filings
- Professional layouts: Matches Bloomberg/FactSet conventions

**Audit Trail Contents:**
```python
{
    "query": "...",
    "plan": [...],
    "tool_results": [...],
    "execution_log": [...],
    "metrics": {
        "overall_confidence": 0.85,
        "latency_ms": 3421,
        "success_rate": 1.0
    }
}
```

**Interview Talking Point:**
> "The reporter isn't just a formatter - it's the observability layer. Every response includes a complete audit trail showing what tools were called, what data sources were used, confidence scores, and execution time. In finance, you need to show your work. This audit trail means a user can verify where every number came from."

---

### 5. LangGraph Workflow (`agent/graph.py`)

**Purpose:** Orchestrate the flow between nodes

**How It Works:**
```python
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("reporter", reporter_node)

# Define flow
workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "reporter")
workflow.add_edge("reporter", END)

# Compile
graph = workflow.compile()

# Run
result = graph.invoke(initial_state)
```

**Why LangGraph?**
- Industry standard for agentic systems
- Makes flow explicit and visible
- Handles state passing automatically
- Easy to add conditional routing (Phase 3: validation loops)
- Type-safe state merging

**Interview Talking Point:**
> "I use LangGraph because it makes the agent flow explicit and testable. You can literally draw the flow diagram from the code. It also makes it trivial to add complex patterns like validation loops or retry logic - just add nodes and conditional edges. This is the same pattern used by LangChain agents in production."

---

## Data Flow Example

**Query:** "What was Tesla's revenue last quarter?"

**Step 1 - Planner:**
```python
Input: {query: "What was Tesla's revenue last quarter?"}

LLM Reasoning:
- User asking about quarterly revenue
- Need financial data
- Use SEC tool

Output: {
    plan: [{
        tool_name: "get_quarterly_financials",
        parameters: {ticker: "TSLA"},
        reason: "Extract revenue from latest 10-Q"
    }],
    reasoning: "Single tool call to get XBRL data"
}
```

**Step 2 - Executor:**
```python
Input: plan from Step 1

For each step:
1. Route "get_quarterly_financials" → sec_analyzer.py
2. Call get_latest_quarterly_financials("TSLA")
3. Tool fetches 10-Q via edgartools
4. Extracts XBRL tags (us-gaap:Revenues)
5. Returns ToolResult

Output: {
    tool_results: [{
        tool_name: "get_quarterly_financials",
        data: {
            revenue: 25167000000,
            net_income: 2167000000,
            ...
        },
        source: "https://sec.gov/...",
        confidence: 1.0,
        success: True
    }]
}
```

**Step 3 - Reporter:**
```python
Input: tool_results from Step 2

Processing:
1. Format currency: 25167000000 → $25.17B
2. Add confidence indicator: 1.0 → 🟢
3. Create audit trail
4. Calculate metrics

Output: {
    answer: "
# Analysis Results
**Company:** Tesla, Inc.
**Revenue:** $25.17B
**Source:** SEC 10-Q Filing
**Confidence:** 100% 🟢
",
    audit_trail: {...},
    overall_confidence: 1.0
}
```

---

## Technology Stack

### Core Framework
- **LangGraph** (0.2.50) - State machine orchestration
- **LangChain Core** (0.3.28) - Base abstractions

### LLMs
- **Gemini 2.0 Flash** - Planning (via langchain-google-genai)
- Fast, accurate, cost-effective
- 78% on SWE-bench Verified

### Data Sources

#### SEC Financial Data
- **edgartools** (2.28.0) - XBRL extraction
- Official SEC EDGAR database
- Confidence: 1.0 (audited data)

#### Competitor Discovery
- **Polygon.io API** - Professional financial data
  - Primary source
  - Real-time, SIC code classification
  - Confidence: 0.85
  - Rate limited: 5/min, 250/day (free tier)

- **yfinance** (0.2.50) - Yahoo Finance fallback
  - Backup source
  - Free, unlimited
  - Confidence: 0.8
  - Graceful degradation

### Future (Phase 2)
- **Tavily** - Web search for general research
- More data sources as needed

### Infrastructure
- **Python 3.10+** - Modern syntax (match, type hints)
- **pydantic** - Data validation
- **python-dotenv** - Configuration management

---

## Key Innovations

### 1. Cascading Data Sources with Graceful Degradation

**The Problem:**
- Professional APIs (Polygon.io) have rate limits
- Can't risk demo failure
- But want to show professional integration skills

**The Solution:**
```python
try:
    return fetch_from_polygon()  # Try professional API
except RateLimitException:
    return fetch_from_yfinance()  # Seamless fallback
```

**Why This Is Impressive:**
- Shows understanding of production systems
- Demonstrates fault tolerance
- This is how Bloomberg Terminal works (multiple data feeds)
- User always gets answer
- Even failure scenarios become talking points

### 2. Confidence Scoring System

**The Innovation:**
Different data sources have different quality levels:

| Source | Confidence | Why |
|--------|-----------|-----|
| SEC XBRL | 1.0 | Official, audited filings |
| Polygon.io | 0.85 | Professional API, real-time |
| yfinance | 0.8 | Reliable but unofficial |
| Web search | 0.7 | LLM synthesis, multiple sources |
| Stale cache | 0.5 | Outdated but verified |

**Usage:**
- Color-code in UI (🟢🟡🔴)
- Trigger validation if overall_confidence < 0.6
- Show in audit trail
- Helps users trust the data

**Why This Matters:**
- Financial analysts care about data quality
- Shows understanding of data provenance
- Production systems track confidence (Bloomberg, FactSet)

### 3. Complete Audit Trails

**The Problem:**
- Financial decisions need provenance
- Need to verify where data came from
- Debugging requires execution traces

**The Solution:**
Every response includes:
```python
{
    "query": "...",
    "plan": [...],           # What we planned
    "tool_results": [...],   # What we executed
    "execution_log": [...],  # Step-by-step trace
    "metrics": {
        "confidence": 0.85,
        "latency": 3421,
        "success_rate": 1.0
    },
    "data_sources": [...],   # Where data came from
    "timestamps": {...}
}
```

**Why This Is Production-Grade:**
- Compliance requirements (show your work)
- Debugging (see exactly what happened)
- Monitoring (track confidence, latency)
- User trust (transparency)

### 4. XBRL Over PDF Parsing

**The Decision:**
Instead of parsing PDFs with OCR/regex, use structured XBRL data

**Why This Matters:**
```
PDF Approach (Bad):
- OCR errors
- Table breaks across pages
- Regex brittle
- Format changes between filings
- Confidence: 0.6

XBRL Approach (Good):
- Structured XML
- Standard GAAP tags
- Zero extraction errors
- Official SEC format
- Confidence: 1.0
```

**Interview Talking Point:**
> "I chose XBRL over PDF parsing because it's structured, official, and error-free. This is the same approach Bloomberg and FactSet use. When you're dealing with financial data, accuracy is everything. PDF parsing might be 95% accurate, but in finance, you need 100%."

---

## Scalability & Production Considerations

### Current Limitations
- Single-threaded execution (tools run sequentially)
- No retry logic yet (Phase 3)
- Limited to S&P 500 companies
- Free tier rate limits

### Production Migration Path

1. **Scaling Data Sources**
   - Upgrade to Polygon.io paid tier ($200/month)
     - 1000 calls/minute vs. 5
     - Real-time data vs. 15-min delay
   - Add FactSet or Bloomberg API
   - Add database of all public companies (not just S&P 500)

2. **Add Validation Layer** (Phase 3)
   - Data completeness checks
   - Freshness validation (flag data >90 days old)
   - Cross-source verification
   - Retry logic (max 1 retry)

3. **Parallelization**
   - Use asyncio for concurrent tool calls
   - "Get revenue for AAPL, GOOGL, MSFT" → 3 parallel API calls
   - 3x faster for multi-company queries

4. **Caching Strategy**
   - Redis for distributed cache
   - TTL based on data type:
     - Company info: 24 hours
     - Stock prices: 15 minutes
     - SEC filings: 7 days
   - Cache warming for common queries

5. **Monitoring**
   - Track confidence trends
   - Alert on fallback rate >10%
   - Monitor API latencies
   - Log all rate limit hits

6. **Cost Optimization**
   - Use free tiers first (yfinance)
   - Upgrade to paid only when needed
   - Monitor fallback rate to know when to upgrade
   - Example: If falling back 10% of time → upgrade

---

## Testing Strategy

### Pre-Demo Testing
```bash
# Run full system test
python test_complete_flow.py

# Pre-cache all demo data
python precache_competitors.py

# Verify cache
ls -la .cache/
```

### Demo Queries (Prepared)
1. "What was Apple's revenue last quarter?" (Simple)
2. "Find Tesla's competitors and their revenues" (Complex)
3. "Top 5 tech companies" (Phase 2)
4. Edge case: Invalid ticker (Error handling)

### Backup Plan
- All data pre-cached
- Screenshots of successful runs
- Can show code/architecture even if network fails

---

## Interview Talking Points Summary

### On Architecture:
> "I use LangGraph's state machine pattern with three core nodes: Planner, Executor, Reporter. The state flows through like an assembly line, with each node doing one job well. This separation of concerns makes the system easy to test, debug, and extend."

### On Data Quality:
> "I implemented a confidence scoring system because financial analysts need to know data quality. SEC XBRL gets 1.0 (official filings), Polygon.io gets 0.85 (professional API), yfinance gets 0.8 (reliable but unofficial). This is shown in the UI and used for validation."

### On Fault Tolerance:
> "The competitor finder uses cascading data sources - try Polygon.io first, fall back to yfinance if it fails. This is the same pattern Bloomberg Terminal uses. Even if the primary feed goes down, the system still works. In the interview, if Polygon hits its rate limit, that's actually great - I can show the fallback working."

### On Production Readiness:
> "This isn't just a demo - it's architected for production. Complete audit trails for compliance, confidence scoring for trust, graceful degradation for reliability. To scale, you'd add a validation layer, parallelize tool calls, and upgrade to paid APIs. The foundation is already production-grade."

---

## Files Reference
```
sagard-sentinel/
├── agent/
│   ├── state.py          # AgentState schema, ToolResult types
│   └── graph.py          # LangGraph workflow orchestration
├── nodes/
│   ├── planner.py        # LLM-based query decomposition
│   ├── executor.py       # Tool routing and execution
│   └── reporter.py       # Professional formatting + metrics
├── tools/
│   ├── sec_analyzer.py   # XBRL financial data (confidence: 1.0)
│   └── competitor_finder.py  # Cascading data sources (0.8-0.85)
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md     # This file
│   ├── DESIGN_DECISIONS.md        # Why we made each choice
│   ├── INTERVIEW_GUIDE.md         # Talking points
│   └── QUICK_REFERENCE.md         # One-pagers
└── tests/
    └── test_complete_flow.py  # End-to-end validation
```

---

## Next Steps (Phase 2 - Saturday)

1. Implement remaining tools:
   - `get_top_companies` - Market cap rankings
   - `research_ai_disruption` - Tavily web search
   - `general_financial_research` - Fallback tool

2. Build Streamlit UI (Phase 3 - Sunday):
   - Query input
   - Audit trail viewer
   - Confidence visualization
   - Download results

3. Final Polish (Monday):
   - System design diagram
   - Practice demo (time to 15 mins)
   - Prepare backup screenshots

---

**Status:** Phase 1 Complete ✅ | Core Architecture Solid 💪 | Ready for Interview 🚀