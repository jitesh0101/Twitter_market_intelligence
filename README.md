# Twitter Market Intelligence System

A production-grade system for collecting and analyzing Twitter/X data for real-time market intelligence and algorithmic trading signals. This system scrapes Indian stock market discussions without using paid APIs and transforms textual data into quantitative trading signals.

##  Project Overview

This assignment demonstrates:
- **Advanced Web Scraping**: Selenium-based scraping with sophisticated anti-detection measures
- **Data Engineering**: Efficient data structures, deduplication, and Parquet storage
- **System Design**: Scalable, maintainable architecture following SOLID principles
- **Production Quality**: Comprehensive logging, error handling, and configuration management

##  Current Status: Part 1 Complete (50%)

###  Implemented Components

1. **Scraping Infrastructure** (`src/scraper/`)
   - Selenium-based Twitter scraper with undetected-chromedriver
   - Anti-detection mechanisms (stealth mode, user agent rotation, human-like behavior)
   - Rate limiting and retry logic
   - Checkpoint system for resumable scraping

2. **Data Processing** (`src/processor/`)
   - Data cleaning and normalization
   - Multi-strategy deduplication (content hash, fuzzy matching)
   - Unicode handling for Indian language content
   - Efficient Parquet storage with compression

3. **Utilities** (`src/utils/`)
   - Colored logging with file rotation
   - YAML configuration with environment variable overrides
   - Helper functions for common operations
   - Memory monitoring and performance tracking

4. **Configuration Management**
   - YAML-based configuration
   - Environment variable support
   - Validation and type checking

###  Upcoming in Part 2 (50%)

- NLP analysis and text processing
- Sentiment analysis
- Signal generation for trading
- Memory-efficient visualization
- Main orchestrator script
- Complete documentation

## ️ Architecture

```
twitter-market-intelligence/
├── src/
│   ├── scraper/           # Web scraping with Selenium
│   │   ├── twitter_scraper.py
│   │   └── anti_detection.py
│   ├── processor/         # Data cleaning and storage
│   │   ├── data_cleaner.py
│   │   ├── deduplicator.py
│   │   └── storage.py
│   ├── analyzer/          # [Part 2] NLP and signal generation
│   └── utils/             # Common utilities
│       ├── logger.py
│       ├── config.py
│       └── helpers.py
├── data/
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Cleaned data
│   └── analysis/         # Analysis results
├── config.yaml           # Configuration
├── requirements.txt      # Dependencies
└── tests/               # Unit tests
```

##  Quick Start

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser
- 2GB+ RAM recommended

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd twitter-market-intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit configuration if needed
nano config.yaml
```

### Basic Usage

```python
from src import TwitterScraper, DataCleaner, Deduplicator, ParquetStorage
from src.utils import load_config, setup_logging

# Load configuration
config = load_config("config.yaml")
logger = setup_logging(config.get_all())

# Initialize components
scraper = TwitterScraper(config.get_all(), logger)
cleaner = DataCleaner(config.get_all(), logger)
deduplicator = Deduplicator(config.get_all(), logger)
storage = ParquetStorage(config.get_all(), logger)

# Scrape tweets
with scraper:
    tweets = scraper.scrape_hashtags(
        hashtags=["#nifty50", "#sensex", "#banknifty"],
        target_count=2000,
        time_window_hours=24
    )

# Process data
cleaned_tweets = cleaner.clean_batch(tweets)
unique_tweets = deduplicator.deduplicate(cleaned_tweets)

# Save to Parquet
storage.save_processed_tweets(unique_tweets)

logger.info(f"Successfully processed {len(unique_tweets)} tweets")
```

## ️ Configuration

### config.yaml

Key configuration sections:

```yaml
scraper:
  hashtags: ["#nifty50", "#sensex", "#intraday", "#banknifty"]
  target_tweets: 2000
  browser:
    headless: true
  anti_detection:
    random_delays:
      min: 2
      max: 5

processor:
  deduplication:
    method: "content_hash"  
  
storage:
  parquet:
    compression: "snappy"
```

### Environment Variables

Create a `.env` file:

```bash
LOG_LEVEL=INFO
HEADLESS_MODE=true
TARGET_TWEETS=2000
```

##  Technical Implementation

### Anti-Detection Strategy

Our scraper implements multiple layers of anti-detection:

1. **Undetected ChromeDriver**: Bypasses basic automation detection
2. **User Agent Rotation**: Randomizes browser fingerprints
3. **Human-like Behavior**: Random scrolling, delays, mouse movements
4. **Rate Limiting**: Respects platform limits
5. **Stealth Scripts**: Hides WebDriver properties

### Data Structures

- **Efficient Storage**: Parquet format with Snappy compression (3-5x smaller than CSV)
- **Deduplication**: Content hashing (O(n)) for exact matches, Jaccard similarity for fuzzy matching
- **Memory Management**: Chunked processing for large datasets

### Performance Optimization

- Concurrent processing support (configurable workers)
- Generator patterns for memory efficiency
- Checkpoint system for resumable operations
- Incremental file writes

##  Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_basic.py::test_deduplication -v
```

##  Troubleshooting

### Common Issues

**Chrome Driver Issues:**
```bash
# The undetected-chromedriver should auto-download, but if issues occur:
pip install --upgrade undetected-chromedriver
```

**Memory Issues:**
```yaml
# Adjust in config.yaml
performance:
  memory_limit_mb: 1024  # Reduce if needed
  chunk_size: 500
```

**Rate Limiting:**
```yaml
# Slow down requests in config.yaml
scraper:
  rate_limit:
    requests_per_minute: 20  # Reduce from 30
```

##  Legal & Ethical Considerations

️ **Important**: This project is for educational purposes only.

- Web scraping may violate Twitter's Terms of Service
- Use responsibly and respect rate limits
- Do not use for commercial purposes without proper authorization
- Consider using official APIs for production systems

##  Data Schema

### Raw Tweet Structure

```python
{
    'tweet_id': str,           # Unique hash
    'username': str,           # Twitter username
    'timestamp': str,          # ISO format datetime
    'content': str,            # Tweet text
    'hashtags': List[str],     # Extracted hashtags
    'mentions': List[str],     # Extracted mentions
    'likes': int,              # Like count
    'retweets': int,           # Retweet count
    'replies': int,            # Reply count
    'views': int,              # View count
    'scraped_at': str          # When scraped
}
```

##  Key Learnings & Design Decisions

### Why These Choices?

1. **Selenium over BeautifulSoup/Scrapy**: Twitter heavily uses JavaScript rendering
2. **Undetected ChromeDriver**: Best success rate bypassing anti-bot measures
3. **Parquet over CSV**: 3-5x space savings, maintains data types, faster reads
4. **Content Hashing**: Most reliable deduplication method for exact matches
5. **Checkpoint System**: Critical for long-running scrapes (can take 2-4 hours for 2000 tweets)

##  Performance Metrics

Expected performance on standard hardware:

- **Scraping Speed**: 50-100 tweets/minute (with rate limiting)
- **Memory Usage**: ~500MB for 2000 tweets
- **Storage Size**: ~1-2MB (Parquet) vs ~5-10MB (CSV)
- **Processing Time**: <10 seconds for 2000 tweets

##  Next Steps (Part 2)

1. Implement NLP analysis module
2. Build signal generation system
3. Create visualization components
4. Develop main orchestrator
5. Complete comprehensive documentation
6. Add advanced features (sentiment analysis, trend detection)

## ‍ Development

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

### Project Structure

- **Modular Design**: Each component is independent and testable
- **Configuration-Driven**: All settings externalized
- **Logging**: Comprehensive logging at all levels
- **Error Handling**: Graceful degradation with retry logic

##  License

MIT License - See LICENSE file for details

##  Contributing

This is an assignment project, but feedback welcome!

---

**Status**: Part 1 Complete  | Part 2 In Progress 

Last Updated: 2025-10-31
