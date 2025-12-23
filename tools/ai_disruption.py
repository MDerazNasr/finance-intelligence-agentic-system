"""
AI Disruption Analyzer - Research Tool for Industry AI Trends

This tool performs web research to identify how AI is disrupting
a given industry and what the key use cases are.

Unlike tools 1-3 which fetch structured data, this tool:
1. Searches the web for information
2. Reads and synthesizes multiple sources
3. Returns qualitative analysis

Technology stack:
- Tavily: Web search API for AI agents
- Gemini: LLM for synthesis
- Confidence: 0.7 (lower than direct data sources)
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# Cache configuration
CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_DURATION_HOURS = 24  # AI trends change, but not daily

def research_ai_disruption(industry: str) -> Dict[str, Any]:
    """
    Research how AI is disrupting an industry.
    
    Algorithm:
    1. Check cache (24 hours)
    2. Search web via Tavily
    3. Synthesize findings via Gemini
    4. Structure as use cases + analysis
    5. Return with confidence 0.7
    
    Args:
        industry: Industry to research (e.g., "healthcare", "finance")
        
    Returns:
        ToolResult with:
        - summary: Overview of AI disruption
        - use_cases: List of specific AI applications
        - examples: Companies/projects implementing AI
        - sources: URLs of articles used
        
    Example:
        result = research_ai_disruption("healthcare")
        # Returns analysis of AI in healthcare with use cases
    """

    start_time = time.time()

    try:
        print(f"\n🔍 Researching AI disruption in {industry}...")
        
        # Step 1: Check cache
        cache_key = f"ai_disruption_{industry.lower()}"
        cached = _get_from_cache(cache_key)
        if cached:
            # Validate cached structure to avoid NoneType errors
            if isinstance(cached, dict) and cached.get("data") is not None:
                print("  💾 Using cached research")
                elapsed = time.time() - start_time
                if elapsed < 0.5:
                    time.sleep(0.5 - elapsed)
                return cached
            else:
                print("  ⚠️ Cached research invalid, re-fetching...")
        
        # Step 2: Search the web
        print("  🌐 Searching the web...")
        search_results = _search_web(industry)
        
        if not search_results:
            return _create_error_result(
                industry,
                "Web search failed - check Tavily API key or network connection"
            )
        
        # Step 3: Synthesize with LLM
        print("  🤖 Synthesizing findings with LLM...")
        analysis = _synthesize_with_llm(industry, search_results)
        
        if not analysis:
            return _create_error_result(
                industry,
                "LLM synthesis failed - check Gemini API key"
            )

        # Ensure required fields exist to avoid NoneType errors downstream
        analysis.setdefault("summary", "")
        analysis.setdefault("use_cases", [])
        analysis.setdefault("examples", [])
        analysis.setdefault("sources", [])
        analysis["industry"] = industry
        
        # Step 4: Structure result
        result = {
            'tool_name': 'research_ai_disruption',
            'parameters': {'industry': industry},
            'data': analysis,
            'source': f"Web research + LLM synthesis ({len(search_results)} sources)",
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': 0.7,  # Lower than direct data (this is research/synthesis)
            'success': True,
            'error': None
        }
        
        # Cache it
        _save_to_cache(cache_key, result)
        
        # Ensure minimum delay
        elapsed = time.time() - start_time
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)
        
        return result
    except Exception as e:
        # Catch-all to avoid NoneType errors in the agent pipeline
        print(f"  ❌ Unexpected error: {e}")
        return _create_error_result(industry, f"Unexpected error: {e}")

def _search_web(industry: str) -> List[Dict[str, Any]]:
    """
    Search the web for AI disruption information using Tavily.
    
    Returns list of search results with:
    - title: Article title
    - url: Link to article
    - content: Excerpt/snippet
    - score: Relevance score
    """
    
    try:
        
        # Get API key
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("    ⚠️ TAVILY_API_KEY not found in environment")
            return []
        
        # Initialize client
        tavily = TavilyClient(api_key=api_key)
        
        # Construct search query
        # Be specific to get high-quality results
        query = f"AI artificial intelligence disruption {industry} industry use cases applications"
        
        print(f"    📡 Query: '{query}'")
        
        # Search
        response = tavily.search(
            query=query,
            search_depth="advanced",  # More thorough search
            max_results=5,            # 5 high-quality sources
            include_domains=[],       # No restrictions
            exclude_domains=[]        # No exclusions
        )
        
        # Extract results
        results = response.get('results', [])
        
        print(f"    ✅ Found {len(results)} sources")
        
        return results
    
    except ImportError:
        print("    ❌ Tavily not installed: pip install tavily-python")
        return []
    
    except Exception as e:
        print(f"    ❌ Search failed: {str(e)}")
        return []

def _synthesize_with_llm(industry: str, search_results: List[Dict]) -> Dict[str, Any]:
    """
    Use Gemini to synthesize search results into structured analysis.
    
    Returns:
    {
        'summary': str,              # Overview of AI disruption
        'use_cases': List[str],      # 5-7 specific use cases
        'examples': List[Dict],      # Companies/projects
        'sources': List[Dict]        # Source URLs
    }
    """
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("    ⚠️ GOOGLE_API_KEY not found")
            return None
        
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.3,  # Slightly creative but mostly factual
            google_api_key=api_key
        )
        
        # Build context from search results
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"""
    Source {i}: {result.get('title', 'Unknown')}
    URL: {result.get('url', '')}
    Content: {result.get('content', '')[:500]}
    """)
            
            context = "\n\n".join(context_parts)
            
            # Create synthesis prompt
            prompt = f"""You are a technology analyst researching AI disruption in the {industry} industry.

    Based on these search results, create a comprehensive analysis:

    {context}

    Provide your analysis in the following JSON format:
    {{
        "summary": "2-3 sentence overview of how AI is disrupting this industry",
        "use_cases": [
            "Specific use case 1 with brief explanation",
            "Specific use case 2 with brief explanation",
            "Specific use case 3 with brief explanation",
            "Specific use case 4 with brief explanation",
            "Specific use case 5 with brief explanation"
        ],
        "examples": [
            {{"company": "Company name", "application": "What they're doing with AI"}},
            {{"company": "Company name", "application": "What they're doing with AI"}},
            {{"company": "Company name", "application": "What they're doing with AI"}}
        ]
    }}

    Requirements:
    - Be specific and concrete
    - Use information from the sources provided
    - Include 5-7 use cases
    - Include 3-5 real company examples
    - Keep it factual and accurate
    - Output ONLY valid JSON (no markdown, no preamble)
    """
        
        # Call LLM
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        
        # Parse JSON response
        response_text = response.content.strip()
        
        # Remove markdown if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        analysis = json.loads(response_text)
        
        # Add sources
        analysis['sources'] = [
            {
                'title': r.get('title', 'Unknown'),
                'url': r.get('url', ''),
                'score': r.get('score', 0)
            }
            for r in search_results
        ]
        
        print(f"    ✅ Generated {len(analysis.get('use_cases', []))} use cases")
        
        return analysis
    
    except json.JSONDecodeError as e:
        print(f"    ❌ Failed to parse LLM response as JSON: {e}")
        print(f"    Response was: {response_text[:200]}")
        return None
    
    except Exception as e:
        print(f"    ❌ Synthesis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
#Helper functions
def _get_from_cache(cache_key: str) -> Optional[Dict]:
    """Read from cache if fresh (24 hours)"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            
            cache_time = datetime.fromisoformat(cached['cached_at'])
            age = datetime.now() - cache_time
            
            if age < timedelta(hours=CACHE_DURATION_HOURS):
                result = cached.get('result')
                # Ensure result has the expected keys
                if result and isinstance(result, dict) and result.get("success") is not None:
                    return result
        except:
            pass
    
    return None

def _save_to_cache(cache_key: str, result: Dict):
    """Save to cache"""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    try:
        with open(cache_file, 'w') as f:
            json.dump({
                'result': result,
                'cached_at': datetime.now().isoformat()
            }, f, default=str)
    except:
        pass

def _create_error_result(industry: str, error: str) -> Dict:
    """Standard error format"""
    return {
        'tool_name': 'research_ai_disruption',
        'parameters': {'industry': industry},
        'data': None,
        'source': 'ai_disruption',
        'timestamp': datetime.utcnow().isoformat(),
        'confidence': 0.0,
        'success': False,
        'error': error
    }