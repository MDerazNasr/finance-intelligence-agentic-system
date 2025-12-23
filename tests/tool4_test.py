# Simple test

import os
import sys
from pathlib import Path

# Load environment variables
#load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.ai_disruption import research_ai_disruption

result = research_ai_disruption("healthcare")

if result['success']:
    data = result['data']
    print(f"Summary: {data['summary']}")
    print(f"Use cases: {len(data['use_cases'])}")
    print(f"Examples: {len(data['examples'])}")
    print(f"Sources: {len(data['sources'])}")