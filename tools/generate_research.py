"""
General Financial Research Tool - The Fallback

This tool handles queries outside the 4 core use cases.
It's like a "catch-all" that uses web search + LLM synthesis.

Why we need this:
- Real analysts ask hundreds of different questions
- We can't build specialized tools for everything
- But we can't just say "I don't know" either

How it works:
1. Search the web for the query (using Tavily)
2. Use Claude to read the results and synthesize an answer
3. Return with lower confidence (0.7) since it's derived data

Examples of what this handles:
- "What's Apple's P/E ratio?"
- "What did the CEO say in the earnings call?"
- "What are Tesla's risk factors?"
- "Compare margins between Ford and GM"
"""

import os
from typing import Dict, Any
from datetime import datetime
from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

def general_financial_research(query: str) -> Dict[str, Any]:
    """
    Fallback research tool for queries outside the 4 core use cases.
    
    Args:
        query: Any financial question
        
    Returns:
        ToolResult with synthesized answer and sources
    """
    try:
        # Initialize Tavily (web search)
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            raise ValueError("TAVILY_API_KEY not found")
        
        tavily = TavilyClient(api_key=tavily_key)
        
        # Search the web
        search_results = tavily.search(
            query=query,
            search_depth="advanced",  # More thorough search
            max_results=5             # Top 5 results
        )
        
        # Extract relevant info from search results
        sources = []
        context = []
        
        for result in search_results.get("results", []):
            sources.append({
                "title": result.get("title"),
                "url": result.get("url"),
                "snippet": result.get("content", "")[:200]
            })
            context.append(result.get("content", ""))
        
        #Use gemini to get answers 
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            google_api_key="your-api-key-here"
        )
        
        synthesis_prompt = f"""Based on these web search results, answer the question concisely and accurately.

Question: {query}

Search Results:
{chr(10).join(context)}

Provide a clear, factual answer. Cite which sources you used. If the data is contradictory or unclear, mention that."""

        response = llm.invoke([HumanMessage(content=synthesis_prompt)])
        answer = response.content
        
        return {
            "tool_name": "general_financial_research",
            "parameters": {"query": query},
            "data": {
                "answer": answer,
                "sources": sources,
                "search_query": query
            },
            "source": "Web Search + LLM Synthesis",
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.7,  # Lower than XBRL (1.0) or market APIs (0.8)
            "success": True,
            "error": None
        }
        
    except Exception as e:
        return {
            "tool_name": "general_financial_research",
            "parameters": {"query": query},
            "data": None,
            "source": "general_research",
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": 0.0,
            "success": False,
            "error": str(e)
        }