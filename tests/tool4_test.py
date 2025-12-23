# Simple test

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
#load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment (.env) if present
load_dotenv()

from tools.ai_disruption import research_ai_disruption
 
result = research_ai_disruption("healthcare")

if result['success']:
    data = result['data']
    print(f"Summary: {data['summary']}")
    print(f"Use cases: {len(data['use_cases'])}")
    print(f"Examples: {len(data['examples'])}")
    print(f"Sources: {len(data['sources'])}")

    # Simple formatted view (avoid importing reporter to prevent circular imports)
    print("\n--- FORMATTED RESULT ---")
    print(f"Topic: AI disruption in {data.get('industry', 'industry')}")
    print(f"\nSummary:\n{data['summary']}\n")
    print("Top Use Cases:")
    for i, uc in enumerate(data.get('use_cases', [])[:3], 1):
        print(f"  {i}. {uc}")
    print("\nTop Examples:")
    for i, ex in enumerate(data.get('examples', [])[:3], 1):
        print(f"  {i}. {ex}")