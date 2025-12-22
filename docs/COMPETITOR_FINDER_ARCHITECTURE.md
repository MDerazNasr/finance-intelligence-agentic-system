# Competitor Finder Architecture

## Overview

The competitor finder uses a **cascading data source pattern** with graceful degradation:
```
┌─────────────────────────────────────────┐
│         find_competitors(ticker)        │
└────────────────┬────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ Has Polygon   │
         │   API key?    │
         └───┬───────┬───┘
             │       │
         Yes │       │ No
             │       │
             ▼       ▼
    ┌─────────────┐ ┌─────────────┐
    │  Try        │ │  Use        │
    │  Polygon.io │ │  yfinance   │
    └──────┬──────┘ └──────┬──────┘
           │                │
      Success? No           │
           │                │
           ▼                │
    ┌─────────────┐        │
    │  Fallback   │        │
    │  to         │        │
    │  yfinance   │        │
    └──────┬──────┘        │
           │                │
           └────────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  Return       │
            │  Result with  │
            │  Metadata     │
            └───────────────┘
```

## Why This Architecture?

### 1. Professional Data Source (Polygon.io)
- Industry-standard API used by real fintech companies
- Real-time, high-quality data
- Proper SIC code classification
- Shows API integration skills in interview

### 2. Reliable Fallback (yfinance)
- Free and unlimited
- Never fails (important for demos)
- Good enough for POC/development
- 15-minute delayed data

### 3. Graceful Degradation
- If Polygon fails (rate limit, error, timeout), seamlessly switch to yfinance
- User always gets an answer
- Transparent metadata shows which source was used
- This is how real financial systems work (Bloomberg, trading platforms)

## Data Sources Comparison

| Feature | Polygon.io | yfinance |
|---------|-----------|----------|
| **Type** | Professional API | Web scraper |
| **Cost** | Free tier: 5/min, 250/day | Free, unlimited |
| **Data Quality** | Real-time (paid), 15-min delay (free) | 15-min delay |
| **Reliability** | High (proper API) | Medium (could break) |
| **Support** | Yes (docs, SDK) | Community only |
| **Use Case** | Production | Development/POC |
| **Interview Impact** | ✅ Impressive | ⚠️ Adequate |

## Implementation Details

### Caching Strategy

Both sources use aggressive caching:
- **Ticker info:** 24 hours (company data doesn't change daily)
- **Competitor results:** 24 hours (industry doesn't change daily)
- **S&P 500 list:** 30 days (index changes quarterly)

This ensures:
- Fast responses (most queries use cache)
- Low API usage (avoid rate limits)
- Demo reliability (pre-cache everything)

### Rate Limiting

**Polygon.io Free Tier:**
- 5 calls per minute
- 250 calls per day
- Tracked in-memory to avoid exceeding limits
- Falls back to yfinance if limit reached

**yfinance:**
- No official rate limits
- Small delays (0.1s) to be respectful
- Unlimited for practical purposes

### Error Handling
```python
Try Polygon:
  ├─ Rate limit hit? → Fall back to yfinance
  ├─ API error? → Fall back to yfinance  
  ├─ Timeout? → Fall back to yfinance
  └─ Success? → Return Polygon data

Fall back to yfinance:
  ├─ Success? → Return yfinance data
  └─ Error? → Return error (both sources failed)
```

## Interview Talking Points

### "Why two data sources?"

> "I implemented a cascading data source pattern with graceful degradation. Polygon.io is the professional API that real fintech companies use, so I wanted to show I can integrate with industry-standard tools. But for demo reliability, I added yfinance as a fallback. If Polygon hits its rate limit or has any issues, the system seamlessly switches to yfinance. The user still gets their answer - they might not even realize we switched providers. This is standard practice in production financial systems like Bloomberg Terminal, which has multiple redundant data feeds."

### "What happens if you hit rate limits?"

> "The free tier has 5 calls per minute and 250 per day, which is tight. I implemented three strategies. First, aggressive caching with 24-hour TTL - company data doesn't change daily, so we cache everything. Second, I track rate limits in-memory and fall back to yfinance before hitting the limit. Third, I built a pre-cache script that loads all demo data before the presentation, so we make zero API calls during the actual demo. For production, you'd use Polygon's paid tier which has 1000 calls per minute."

### "Why not just use yfinance?"

> "yfinance works great for POC, but for a finance company interview, I wanted to demonstrate I can work with professional APIs. Polygon.io is what real companies use - it has proper SLAs, documentation, and support. yfinance is just a web scraper that could break if Yahoo changes their site. That said, the fallback pattern means we get the best of both worlds - professional tools when possible, reliability when needed."

## Production Migration

To use this in production:

1. **Upgrade to Polygon paid tier** ($200/month)
   - 1000 calls per minute
   - Real-time data (not 15-min delay)
   - Better SLA and support

2. **Keep yfinance fallback** (always good to have redundancy)

3. **Add monitoring**
   - Track fallback rate
   - Alert if fallback rate > 10%
   - Auto-upgrade if consistently hitting limits

4. **Consider additional providers**
   - FactSet (institutional grade)
   - Bloomberg API (enterprise)
   - AlphaVantage (alternative free tier)

## Testing

Run the pre-cache script:
```bash
python precache_competitors.py
```

This will:
1. Test Polygon.io (if API key set)
2. Test yfinance fallback
3. Cache all demo data
4. Report which source each company used

After running, your demo will be instant (zero API calls).