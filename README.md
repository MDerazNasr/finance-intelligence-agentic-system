# Sagard Analyst Sentinel

**AI-Powered Financial Intelligence Agent | Multi-Source Data Integration | Production-Ready Architecture**

## What This Is

A sophisticated financial analysis agent that answers complex financial questions by automatically routing queries to the right data sources and synthesizing results with confidence scoring.

Ask it: *"What were Apple's top 3 competitors and their Q3 revenues?"*

It will:
1. Identify the query requires competitor data + financials
2. Fetch competitors from market data APIs
3. Extract quarterly revenue from SEC XBRL filings
4. Return formatted answer with confidence scores and audit trail

**3-7 seconds cold start | <1 second cached**

---

## Quick Start

### Installation

```bash
# Clone repo
git clone https://github.com/yourusername/sagard-analyst-sentinel.git
cd sagard-analyst-sentinel

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys:
# - GOOGLE_API_KEY (free from aistudio.google.com)
# - SEC_API_USER_AGENT (your name and email)
# - POLYGON_API_KEY (optional, free tier available)
```

### Run the Demo

```bash
# Start Streamlit dashboard
streamlit run app.py

# Navigate to http://localhost:8501
# Enter a financial query and click "Analyze"
```

### Example Queries

```
What was Apple's revenue last quarter?
→ Confidence: 100% | Source: SEC 10-Q

Find Tesla's top 5 competitors
→ Confidence: 85% | Source: Polygon.io (Professional API)

Top 10 healthcare companies by market cap
→ Confidence: 80% | Source: yfinance

How is AI disrupting the financial sector?
→ Confidence: 70% | Source: Web research synthesis
```

---

## Architecture

### System Design (4-Layer)

```
User Query (Streamlit UI)
    ↓
LangGraph State Machine
    ├─→ Planner (Gemini 2.0 Flash)
    │   └─ Decides: Which tools to use?
    │
    ├─→ Executor (Tool Router)
    │   ├─ SEC Analyzer (edgartools) → 10-Q financials
    │   ├─ Competitor Finder (Polygon + yfinance) → Market data
    │   ├─ Top Companies (yfinance) → Rankings
    │   └─ AI Research (Tavily + Gemini) → Web synthesis
    │
    └─→ Reporter (Formatter)
        └─ Answer + Metrics + Audit Trail
           ↓
        User sees: Answer | Confidence | Latency | Execution Log
```

### Key Design Decisions

| Decision | Why | Benefit |
|----------|-----|---------|
| **LangGraph** | Industry-standard state machine for agents | Explicit flow, testable, easy to extend |
| **Gemini 2.0 Flash** | 78% SWE-bench, 3x faster than alternatives | Fast planning, low cost ($0.001/1K tokens) |
| **SEC XBRL** | Official structured data from SEC | 100% accurate, no OCR errors |
| **Cascading Sources** | Polygon (professional) → yfinance (free fallback) | Always works, no single point of failure |
| **Confidence Scoring** | Track data quality by source | Users know: "Should I trust this number?" |
| **Type Safety** | TypedDict + pydantic validation | Catch errors early, prevent bugs |

---

## Tech Stack

### Core Orchestration
- **LangGraph 0.2.50** - Agentic workflow orchestration
- **LangChain Core 0.3.28** - LLM integrations
- **Python 3.10+** - Modern runtime

### LLM & Planning
- **Gemini 2.0 Flash** - Query decomposition and planning

### Data Sources
- **edgartools 2.28.0** - SEC XBRL extraction (10-Q/10-K)
- **Polygon.io API** - Professional market data
- **yfinance 0.2.50** - Free market data (fallback)
- **Tavily 0.5.0** - AI-optimized web search

### Frontend & Validation
- **Streamlit 1.41.1** - Web dashboard
- **pydantic 2.10.4** - Data validation

### Infrastructure
- **JSON Caching** - 24-hour TTL in `.cache/`
- **python-dotenv** - Environment configuration

---

## How It Works

### 1. Query Understanding (Planner Node)
User enters natural language query. Gemini LLM reads system prompt describing 5 available tools and their purposes, then decides which tools to call.

**Example:**
```
User: "What was Apple's revenue last quarter?"

Planner reasoning:
→ User asking about financial metrics
→ Decision tree: financials → use SEC analyzer
→ Extract parameter: ticker = "AAPL"

Output: {"tool_name": "get_quarterly_financials", "parameters": {"ticker": "AAPL"}}
```

Why LLM instead of rules?
- Handles natural language variations (synonyms, rephrasing)
- Intelligent parameter extraction
- Supports complex multi-tool queries
- Easy to extend (add tool = update system prompt)

### 2. Tool Execution (Executor Node)
Router matches tool name to Python function, executes with error isolation.

**Each tool returns ToolResult:**
```python
{
    "success": bool,
    "data": dict,
    "confidence": float,      # 0.0-1.0 based on source reliability
    "source": str,            # Where data came from
    "error": Optional[str]
}
```

**Confidence by Source:**
- 1.0 = SEC XBRL (official, audited)
- 0.85 = Polygon.io (professional API)
- 0.8 = yfinance (reliable, unofficial)
- 0.7 = Web research (synthesized)
- 0.0 = Tool error (failed execution)

### 3. Formatting & Metrics (Reporter Node)
Format raw data for display, calculate metrics.

**What user sees:**
```
Confidence: 100%
Answer: Apple's revenue was $94.93B (Q3 2024)
Latency: 3.2 seconds
Tools used: SEC Analyzer

Audit Trail (expandable):
- Query analyzed
- Tool routing decision
- SEC EDGAR 10-Q fetched
- XBRL parsed
- Revenue tag extracted
- Result formatted
```

### 4. Error Handling
- One tool failure ≠ system failure
- Failed tools return error ToolResult
- Executor continues with other tools
- Overall confidence reflects partial failures

**Example:**
```
Query: "Top tech companies and their AI disruption impact"

If Competitor Finder fails:
- Top Companies succeeds (confidence 0.8)
- AI Research succeeds (confidence 0.7)
- Overall confidence = 0.75 (partial success)
- User sees answer with caveat
```

---

## Code Structure

```
sagard-analyst-sentinel/
├── app.py                          # Streamlit dashboard
├── agent/
│   ├── graph.py                    # LangGraph state machine
│   ├── state.py                    # AgentState schema
│   └── __init__.py
├── nodes/
│   ├── planner.py                  # Gemini planning node
│   ├── executor.py                 # Tool routing & execution
│   ├── reporter.py                 # Formatting & metrics
│   └── __init__.py
├── tools/
│   ├── sec_analyzer.py             # SEC XBRL extraction
│   ├── competitor_finder.py        # Market data with cascading sources
│   ├── top_companies.py            # Company rankings
│   ├── ai_disruption.py            # Web research synthesis
│   └── __init__.py
├── tests/
│   ├── test_complete_flow.py       # End-to-end tests
│   ├── test_sec_tool.py            # SEC analyzer tests
│   └── test_tool_routing.py        # Tool matching tests
├── .cache/                         # Caching (24h TTL)
├── requirements.txt
├── .env.example
├── README.md
└── docs/
    ├── ARCHITECTURE.md             # Detailed system design
    ├── CONFIDENCE_SCORING.md       # Data quality framework
    └── COMPETITOR_FINDER.md        # Competitor matching logic
```

---

## Performance

### Latency Breakdown

| Phase | Time | What Happens |
|-------|------|--------------|
| Input Processing | 0.1s | Query validation |
| Planning (Gemini) | 1-2s | LLM decides tools |
| Execution (APIs) | 2-5s | Fetch data from sources |
| Formatting | 0.1s | Format answer + metrics |
| **Total (cold)** | **3-7s** | All steps |
| **Total (cached)** | **<1s** | Cache hit, no APIs |

### Caching Strategy

- **First query:** API calls happen (3-7s)
- **Same query within 24h:** Instant from cache (<1s)
- **Demo:** Pre-populate `.cache/` with common queries for zero latency

### Scalability

**Current:** Single-threaded, perfect for demo/prototype

**Phase 2 (Production):**
- Async tool execution (concurrent API calls)
- Redis distributed cache
- PostgreSQL for historical queries
- Load balancer for multiple instances
- Circuit breakers for API failures

---

## Features

### Implemented

✓ Multi-source data integration (SEC + Market Data + Web)  
✓ Cascading data sources (professional → free fallback)  
✓ Confidence scoring by source reliability  
✓ Complete audit trail (full execution trace)  
✓ Error isolation (partial failures handled gracefully)  
✓ Type-safe state management (TypedDict + pydantic)  
✓ Caching with TTL  
✓ Execution logging  
✓ Web dashboard (Streamlit)  

### Planned (Phase 2)

→ REST API (`/api/v1/analyze`)  
→ Database backend (PostgreSQL)  
→ Async/parallel tool execution  
→ Multi-LLM support (Gemini OR Claude)  
→ Advanced retry logic (exponential backoff)  
→ Distributed caching (Redis)  
→ Structured logging (ELK stack)  
→ Monitoring & metrics (Prometheus + Grafana)  

---

## Example Queries

### Financial Data
```
What was Apple's revenue last quarter?
→ Pulls from SEC 10-Q (Confidence: 100%)

Show me Tesla's net income for 2023
→ Aggregates 4 quarterly 10-Qs (Confidence: 100%)

What's Microsoft's operating margin?
→ Calculates from 10-Q data (Confidence: 100%)
```

### Competitive Analysis
```
Find Tesla's main competitors
→ Uses Polygon + yfinance (Confidence: 85%)

Top 10 healthcare companies by market cap
→ Ranks companies by market data (Confidence: 80%)

Who competes with Apple in consumer electronics?
→ Market data + industry research (Confidence: 82%)
```

### Industry Research
```
How is AI disrupting healthcare?
→ Web research synthesis (Confidence: 70%)

What are the latest trends in fintech?
→ Web search + LLM analysis (Confidence: 70%)

Show me companies investing in quantum computing
→ Web + market data synthesis (Confidence: 65%)
```

---

## Testing

### Run Tests

```bash
# All tests
pytest

# Specific test
pytest tests/test_sec_tool.py

# With coverage
pytest --cov=agent --cov=nodes --cov=tools
```

### Test Coverage

- **End-to-end tests** - Full workflow from query to answer
- **Unit tests** - Individual tools (SEC, Polygon, yfinance)
- **Tool routing tests** - LLM decision logic
- **Error handling tests** - Failures and edge cases

---

## API Usage (Phase 2)

When implemented:

```bash
# Query the agent
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was Apple revenue last quarter?",
    "include_audit_trail": true
  }'

# Response
{
  "success": true,
  "answer": "Apple's revenue was $94.93B in Q3 2024",
  "confidence": 1.0,
  "latency_ms": 3200.5,
  "tools_used": ["sec_analyzer"],
  "audit_trail": {...}
}
```

---

## Design Patterns Used

- **State Machine** (LangGraph) - Explicit workflow orchestration
- **Tool Router** - Strategy pattern for tool selection
- **Cascading Fallbacks** - Resilience through data source redundancy
- **Type-Safe State** - TypedDict for compile-time safety
- **Error Isolation** - Graceful degradation on partial failures
- **Confidence Scoring** - Explicit data quality tracking

---

## Production Readiness Checklist

- [x] Clean architecture (separation of concerns)
- [x] Error handling (tool-level isolation)
- [x] Type safety (TypedDict + pydantic)
- [x] Caching strategy (file-based, 24h TTL)
- [x] Audit trail (complete transparency)
- [x] Confidence scoring (data quality tracking)
- [ ] Unit tests (in progress)
- [ ] REST API (Phase 2)
- [ ] Database backend (Phase 2)
- [ ] Monitoring & logging (Phase 2)

---

## Why This Project Matters

### For Hiring Managers

This project demonstrates:

1. **Systems Design Thinking** - Multi-layer architecture, not spaghetti code
2. **Production Mindset** - Error handling, reliability, transparency
3. **Domain Knowledge** - Understands financial data (SEC XBRL, market data)
4. **Real Integration** - Connects to actual APIs (Polygon, SEC, Tavily), not mock data
5. **Code Quality** - Type safety, separation of concerns, clean patterns

### For Data/ML Roles

- Multi-source data integration
- Confidence scoring and data quality
- LLM tool calling and planning
- Error handling and robustness

### For Backend/Systems Roles

- LangGraph orchestration patterns
- Cascading data sources
- Caching strategies
- Type-safe state management
- Scalability thinking (Phase 2 roadmap)

### For Product/Startup Roles

- Solves real problem (financial analysis)
- User-friendly interface (Streamlit)
- Audit trail and transparency (compliance-minded)
- Extensible architecture (easy to add features)

---

## Key Insights

### Why LangGraph?
Not hardcoded if/else rules for tool selection. Gemini LLM understands system prompt describing tools and decides which to use. This makes it flexible, maintainable, and handles complex queries.

### Why Cascading Sources?
Polygon.io is professional but rate-limited (5 calls/min free tier). yfinance is free and unlimited but unofficial. By cascading (try Polygon → fallback to yfinance), we get professional data when possible, always have a backup, and users never see "API failed."

### Why Confidence Scoring?
In finance, users need to know: "Should I trust this?" SEC data is 1.0 because it's official and audited. Polygon is 0.85 (professional but has rate limits). yfinance is 0.8 (reliable but unofficial). Web research is 0.7 (synthesized from noisy sources). Transparency builds trust.

### Why Type Safety?
Python is dynamically typed, which makes typos easy. TypedDict for AgentState and pydantic for ToolResult enforce contracts between components. Catches bugs before they reach production.

---

## What's Next?

**Phase 2 (Coming Soon):**
- REST API for programmatic access
- Database backend (PostgreSQL)
- Async tool execution (10x faster)
- Advanced retry logic
- Distributed caching (Redis)

**Phase 3 (Future):**
- Multi-LLM support
- Custom fine-tuning on financial data
- Real-time monitoring dashboard
- Enterprise features (auth, rate limits, etc)


---

**Made with 🔥 for Georgia Tech & Sagard**
