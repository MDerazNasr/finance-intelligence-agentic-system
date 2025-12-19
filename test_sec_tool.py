# test_sec_tool.py
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from tools.sec_analyzer import get_latest_quarterly_financials

result = get_latest_quarterly_financials("AAPL")
print(f"Success: {result['success']}")
print(f"Confidence: {result['confidence']}")

if result['success']:
    data = result['data']
    print(f"Company: {data['company_name']}")
    print(f"Filing: {data['filing_date']}")
    for key, val in data['financials'].items():
        print(f"{val['label']}: ${val['value']:,.0f}")