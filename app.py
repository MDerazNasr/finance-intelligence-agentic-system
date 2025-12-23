"""
Sagard Financial Analyst Agent - Streamlit Dashboard

This is the main UI for the financial analyst agent.
It provides an interactive web interface for running queries.
"""

import streamlit as st
import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set page config (MUST be first Streamlit command)
st.set_page_config(
    page_title="Sagard Financial Analyst",
    page_icon="🤖",
    layout="wide",  # Use full width
    initial_sidebar_state="expanded"
)

# Environment setup
def setup_environment():
    """
    Ensure all required environment variables are set.
    
    For demo, we load from .env file.
    In production, these would be set in deployment environment.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required keys
    required_keys = {
        'GOOGLE_API_KEY': 'Get from https://aistudio.google.com/',
        'SEC_API_USER_AGENT': 'Format: YourName your.email@example.com',
    }
    
    missing_keys = []
    for key, help_text in required_keys.items():
        if not os.getenv(key):
            missing_keys.append(f"- {key}: {help_text}")
    
    if missing_keys:
        st.error("⚠️ Missing required environment variables:")
        for msg in missing_keys:
            st.write(msg)
        st.info("Add these to your .env file")
        st.stop()

# Run setup
setup_environment()

# Import agent (after environment is set up)
try:
    from agent.graph import run_agent
except ImportError as e:
    st.error(f"Failed to import agent: {e}")
    st.info("Make sure all dependencies are installed: pip install -r requirements.txt")
    st.stop()

# Page header
st.title("🤖 Financial Analyst Agent")
st.markdown("""
Powered by **Gemini 2.0 Flash** with multi-source data integration.

This agent can:
- 📊 Analyze SEC filings (10-Q/10-K)
- 🏢 Find company competitors
- 📈 Rank top companies by market cap
- 🤖 Research AI disruption trends
""")

st.divider()
# Sidebar configuration
with st.sidebar:
    st.header("📚 Example Queries")
    st.markdown("Click any example to run it:")
    
    # Example queries organized by tool
    examples = {
        "SEC Analysis": [
            "What was Apple's revenue last quarter?",
            "Show me Google's net income from their latest 10-Q",
            "What are Microsoft's quarterly financials?",
        ],
        "Competitor Analysis": [
            "Find Tesla's competitors",
            "Who are Apple's main competitors?",
            "Show me competitors for JPMorgan",
        ],
        "Market Rankings": [
            "Top 5 technology companies",
            "Top 10 healthcare companies by market cap",
            "What are the largest financial services companies?",
        ],
        "AI Research": [
            "How is AI disrupting healthcare?",
            "What are AI use cases in finance?",
            "How will AI impact retail industry?",
        ]
    }
    
    # Create buttons for each example
    for category, queries in examples.items():
        st.subheader(category)
        for query in queries:
            if st.button(query, key=query, use_container_width=True):
                st.session_state.query = query
                st.rerun()
    
    st.divider()
    
    # Info section
    st.subheader("ℹ️ About")
    st.markdown("""
    **Tools:**
    - SEC Analyzer (Confidence: 1.0)
    - Competitor Finder (Confidence: 0.8-0.85)
    - Top Companies Ranker (Confidence: 0.8)
    - AI Disruption Research (Confidence: 0.7)
    
    **Data Sources:**
    - SEC EDGAR (XBRL)
    - Polygon.io / yfinance
    - Web search + LLM synthesis
    """)
# Main query input
st.header("💬 Ask a Question")

# Initialize session state for query
if 'query' not in st.session_state:
    st.session_state.query = ""

# Text input with placeholder
query = st.text_input(
    "Enter your financial question:",
    value=st.session_state.query,
    placeholder="e.g., What was Apple's revenue last quarter?",
    help="Ask about financials, competitors, rankings, or AI trends"
)

# Analyze button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze_button = st.button(
        "🔍 Analyze",
        type="primary",
        use_container_width=True
    )
# Execute query when button clicked
if analyze_button and query:
    st.divider()
    
    # Show loading spinner
    with st.spinner("🤖 Agent is thinking..."):
        try:
            # Time the execution
            start_time = datetime.now()
            
            # Run the agent
            result = run_agent(query)
            
            # Calculate actual latency
            end_time = datetime.now()
            actual_latency = (end_time - start_time).total_seconds() * 1000
            
            # Store in session state for display
            st.session_state.result = result
            st.session_state.actual_latency = actual_latency
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)  # Show full traceback in expander
            st.stop()
# Display results if available
if 'result' in st.session_state:
    result = st.session_state.result
    
    st.header("📊 Analysis Results")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        confidence = result.get('overall_confidence', 0)
        st.metric(
            "Confidence",
            f"{confidence:.0%}",
            delta=None,
            help="Average confidence across all data sources used"
        )
    
    with col2:
        latency = st.session_state.get('actual_latency', result.get('total_latency_ms', 0))
        st.metric(
            "Response Time",
            f"{latency:.0f}ms",
            delta=None,
            help="Total time to process query"
        )
    
    with col3:
        tool_results = result.get('tool_results', [])
        successful = sum(1 for t in tool_results if t.get('success'))
        st.metric(
            "Tools Used",
            f"{successful}/{len(tool_results)}",
            delta=None,
            help="Number of tools successfully executed"
        )
    
    with col4:
        retry_count = result.get('retry_count', 0)
        st.metric(
            "Retries",
            str(retry_count),
            delta=None,
            help="Number of retry attempts (if any)"
        )
    
    st.divider()

# Main answer display
    st.subheader("💡 Answer")
    
    answer = result.get('answer', 'No answer generated')
    
    # Display as markdown (this renders the collapsible sources!)
    st.markdown(answer, unsafe_allow_html=True)
    
    st.divider()
# Tool execution details
    st.subheader("🔧 Tool Execution")
    
    tool_results = result.get('tool_results', [])
    
    if tool_results:
        for i, tool_result in enumerate(tool_results, 1):
            with st.expander(f"Tool {i}: {tool_result.get('tool_name', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Status:**", "✅ Success" if tool_result.get('success') else "❌ Failed")
                    st.write("**Confidence:**", f"{tool_result.get('confidence', 0):.0%}")
                    st.write("**Source:**", tool_result.get('source', 'Unknown'))
                
                with col2:
                    st.write("**Parameters:**")
                    st.json(tool_result.get('parameters', {}))
                
                if not tool_result.get('success'):
                    st.error(f"Error: {tool_result.get('error', 'Unknown error')}")
                
                # Show data preview
                if tool_result.get('data'):
                    st.write("**Data Preview:**")
                    # Show first 500 chars of data
                    data_str = str(tool_result['data'])
                    if len(data_str) > 500:
                        st.code(data_str[:500] + "...", language="json")
                    else:
                        st.json(tool_result['data'])
    else:
        st.info("No tools were executed")
# Execution log
    with st.expander("📝 Execution Log"):
        execution_log = result.get('execution_log', [])
        
        if execution_log:
            for log_entry in execution_log:
                st.text(log_entry)
        else:
            st.info("No execution log available")
# Audit trail (complete transparency)
    with st.expander("🔍 Full Audit Trail (JSON)"):
        audit_trail = result.get('audit_trail', {})
        
        if audit_trail:
            st.json(audit_trail)
        else:
            st.info("No audit trail available")
# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>Built with LangGraph + Gemini 2.0 Flash</p>
    <p>Data Sources: SEC EDGAR | Polygon.io | yfinance | Tavily</p>
</div>
""", unsafe_allow_html=True)
"""

---

## 🎨 Complete File Structure

Your `app.py` should now have:
```
1. Imports & page config
2. Environment setup
3. Agent import
4. Page header
5. Sidebar with examples
6. Query input
7. Analyze button
8. Query execution (with spinner)
9. Results display:
   - Metrics cards
   - Answer (with markdown)
   - Tool execution details
   - Execution log
   - Audit trail
10. Footer

"""