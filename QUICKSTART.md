# Quick Start Guide

## Setup (5 minutes)

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
```

## Run the System

### Option 1: Using the Example Script

```bash
python example_usage.py
```

This will:
1. Scrape 2000 tweets for Indian market hashtags
2. Clean and normalize the data
3. Remove duplicates
4. Save to Parquet files

### Option 2: Custom Python Script

```python
from src import TwitterScraper, DataCleaner, Deduplicator, ParquetStorage
from src.utils import load_config, setup_logging

# Load config
config = load_config()
logger = setup_logging(config.get_all())

# Scrape
with TwitterScraper(config.get_all(), logger) as scraper:
    tweets = scraper.scrape_hashtags(
        hashtags=["#nifty50", "#sensex"],
        target_count=500
    )

# Process
cleaner = DataCleaner(config.get_all())
dedup = Deduplicator(config.get_all())

cleaned = cleaner.clean_batch(tweets)
unique = dedup.deduplicate(cleaned)

# Save
storage = ParquetStorage(config.get_all())
storage.save_processed_tweets(unique)

print(f"Processed {len(unique)} unique tweets")
```

## Configuration

Edit `config.yaml` to customize:

```yaml
scraper:
  target_tweets: 2000        # How many tweets to collect
  hashtags:                   # Which hashtags to search
    - "#nifty50"
    - "#sensex"
  browser:
    headless: true           # Run browser in background
```

## Output

Data is saved to:
- **Raw data**: `data/raw/tweets_raw.parquet`
- **Processed data**: `data/processed/tweets_processed.parquet`
- **Logs**: `logs/app.log`
- **Checkpoints**: `data/raw/checkpoints/` (for resuming)

## Viewing Data

```python
import pandas as pd

# Load processed tweets
df = pd.read_parquet("data/processed/tweets_processed.parquet")

print(f"Total tweets: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nSample:\n{df.head()}")

# Basic stats
print(f"\nMost active users:")
print(df['username'].value_counts().head(10))

print(f"\nMost common hashtags:")
print(df.explode('hashtags')['hashtags'].value_counts().head(10))
```

## Troubleshooting

**Scraping takes too long?**
- Reduce `target_tweets` in config.yaml
- Increase `requests_per_minute` (may trigger rate limits)

**Memory issues?**
- Reduce `chunk_size` in config.yaml
- Lower `memory_limit_mb`

**Chrome driver errors?**
```bash
pip install --upgrade undetected-chromedriver
```

**Rate limited?**
- Wait 15-30 minutes
- Reduce scraping speed in config

## Next Steps

After Part 1 completes successfully:
1. Check `data/processed/tweets_processed.parquet`
2. View logs in `logs/app.log`
3. Ready for Part 2 (Analysis & Signals)

## Support

Check the main README.md for:
- Detailed architecture
- Advanced configuration
- Testing instructions
- API documentation
