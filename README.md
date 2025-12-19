# Sagard Analyst Sentinel 🎯

A reliability-first agentic system for financial intelligence. Built for the Sagard AI Enablement internship interview.

## ⚡ Quick Start (Phase 1)

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example env file and add your keys:

```bash
cp .env.example .env
```

Edit `.env` and add:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
SEC_API_USER_AGENT=YourName your.email@example.com
```

**Get API Keys:**
- **Gemini API Key:** https://aistudio.google.com/apikey (Free)
- **SEC User Agent:** Just use your name and email (required by SEC)

### 3. Test Phase 1

```bash
python test_phase1.py
```

This will test:
- ✅ SEC XBRL data extraction (Apple, Google)
- ✅ LangGraph workflow (Plan → Execute → Report)
- ✅ Basic error handling

**Expected output:**
```
✓ Environment variables loaded
✓ Graph created

TEST 1/2
========================================
Query: What was Apple's revenue in their latest quarterly report?

EXECUTION LOG:
🧠 Planning query: ...
📋 Plan created: 1 steps
🔧 Executing 1 tool calls
   ✓ Success (confidence: 1.00)
📊 Generating report

RESULT:
# Analysis Results
**Query:** What was Apple's revenue...
**Company:** Apple Inc.
**Filing Date:** 2024-11-01
...
✓ Test 1 completed successfully!
```

## 🏗️ Project Structure

```
sagard-sentinel/
├── agent/
│   ├── state.py          # Agent memory schema
│   └── graph.py          # LangGraph workflow
├── nodes/
│   ├── planner.py        # Query → Tool plan
│   ├── executor.py       # Execute tools
│   └── reporter.py       # Format output
├── tools/
│   └── sec_analyzer.py   # XBRL financial data (Phase 1 ✅)
├── test_phase1.py        # Phase 1 validation
└── requirements.txt      # Dependencies
```

## 🎯 Phase 1 Complete! ✅

What's working:
- ✅ SEC XBRL extraction (highest quality financial data)
- ✅ LangGraph state machine (Plan → Execute → Report)
- ✅ Gemini 1.5 Flash for planning
- ✅ Structured ToolResult schema with metadata
- ✅ Basic error handling and logging

## 📋 Next: Phase 2 (Saturday)

Implement remaining tools:
1. `competitor_finder.py` - Find company competitors

2. `top_companies.py` - Rank companies by market cap
3. `ai_disruption.py` - Research AI use cases

## 🐛 Troubleshooting

**"GOOGLE_API_KEY not found"**
→ Make sure you created `.env` file with your API key

**"No 10-Q filings found"**
→ Try a different ticker (some companies file 10-K annually instead)

**"ModuleNotFoundError"**
→ Make sure you activated the venv and ran `pip install -r requirements.txt`

**"edgartools error"**
→ Check that SEC_API_USER_AGENT is set in .env (use your real email)

## 💡 Key Design Decisions

1. **Why XBRL over PDF parsing?**
   - Structured, reliable, no OCR errors
   - Official SEC data format
   - Returns actual GAAP accounting tags

2. **Why Gemini Flash?**
   - Fast for planning (low latency)
   - Large context (1M tokens for long filings)
   - Excellent tool calling
   - Cost-effective

3. **Why LangGraph?**
   - Industry standard for agentic workflows
   - Makes validation/retry logic clean
   - Observable state machine

## 📊 Testing Tips

Test with these tickers:
- ✅ AAPL (Apple) - Clean data
- ✅ GOOGL (Google/Alphabet) - Clean data
- ✅ MSFT (Microsoft) - Clean data
- ⚠️ TSLA (Tesla) - Sometimes sparse XBRL tags
- ❌ Private companies - Won't work (no SEC filings)

## 🚀 Demo Prep

Before your interview, test:
1. "What was Apple's revenue last quarter?" (simple)
2. "What was Google's net income in their latest 10-Q?" (specific)
3. Check that XBRL tags are being displayed correctly

---

**Status:** Phase 1 Complete ✅ | Next: Phase 2 Tools 🔧
