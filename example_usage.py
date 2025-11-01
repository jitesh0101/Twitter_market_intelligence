"""
Example usage script for Twitter Market Intelligence System.
This demonstrates how to use the scraping and processing pipeline.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    TwitterScraper,
    DataCleaner,
    Deduplicator,
    ParquetStorage,
    load_config,
    setup_logging,
)


def main():
    """Main execution function."""
    
    # Load configuration
    print("Loading configuration...")
    config = load_config("config.yaml")
    
    # Setup logging
    logger = setup_logging(config.get_all())
    logger.info("=" * 50)
    logger.info("Twitter Market Intelligence System - Part 1")
    logger.info("=" * 50)
    
    # Initialize components
    logger.info("Initializing components...")
    scraper_config = config.get_all()
    
    # Get scraping parameters
    hashtags = config.get("scraper", "hashtags")
    target_tweets = config.get("scraper", "target_tweets")
    time_window = config.get("scraper", "time_window_hours")
    
    logger.info(f"Target: {target_tweets} tweets")
    logger.info(f"Hashtags: {', '.join(hashtags)}")
    logger.info(f"Time window: {time_window} hours")
    
    # Step 1: Scrape tweets
    logger.info("\n" + "=" * 50)
    logger.info("STEP 1: Scraping Tweets")
    logger.info("=" * 50)
    
    try:
        scraper = TwitterScraper(scraper_config, logger)
        
        with scraper:
            tweets = scraper.scrape_hashtags(
                hashtags=hashtags,
                target_count=target_tweets,
                time_window_hours=time_window
            )
        
        logger.info(f" Scraped {len(tweets)} tweets")
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        return 1
    
    if not tweets:
        logger.warning("No tweets collected. Exiting.")
        return 1
    
    # Step 2: Clean data
    logger.info("\n" + "=" * 50)
    logger.info("STEP 2: Cleaning Data")
    logger.info("=" * 50)
    
    try:
        cleaner = DataCleaner(scraper_config, logger)
        cleaned_tweets = cleaner.clean_batch(tweets)
        logger.info(f" Cleaned {len(cleaned_tweets)} tweets")
        
    except Exception as e:
        logger.error(f"Error during cleaning: {e}", exc_info=True)
        return 1
    
    # Step 3: Deduplicate
    logger.info("\n" + "=" * 50)
    logger.info("STEP 3: Deduplication")
    logger.info("=" * 50)
    
    try:
        deduplicator = Deduplicator(scraper_config, logger)
        unique_tweets = deduplicator.deduplicate(cleaned_tweets)
        logger.info(f" {len(unique_tweets)} unique tweets (removed {len(cleaned_tweets) - len(unique_tweets)} duplicates)")
        
    except Exception as e:
        logger.error(f"Error during deduplication: {e}", exc_info=True)
        return 1
    
    # Step 4: Save to Parquet
    logger.info("\n" + "=" * 50)
    logger.info("STEP 4: Saving Data")
    logger.info("=" * 50)
    
    try:
        storage = ParquetStorage(scraper_config, logger)
        
        # Save raw data
        raw_path = storage.save_raw_tweets(tweets)
        logger.info(f" Raw data saved: {raw_path}")
        
        # Save processed data
        processed_path = storage.save_processed_tweets(unique_tweets)
        logger.info(f" Processed data saved: {processed_path}")
        
        # Display file info
        info = storage.get_file_info(processed_path)
        logger.info(f"  - File size: {info['size_mb']} MB")
        logger.info(f"  - Rows: {info['num_rows']}")
        logger.info(f"  - Columns: {info['num_columns']}")
        logger.info(f"  - Compression: {info['compression']}")
        
    except Exception as e:
        logger.error(f"Error during saving: {e}", exc_info=True)
        return 1
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total tweets scraped: {len(tweets)}")
    logger.info(f"After cleaning: {len(cleaned_tweets)}")
    logger.info(f"After deduplication: {len(unique_tweets)}")
    logger.info(f"Data saved to: {processed_path}")
    logger.info("\n Part 1 Complete! Ready for Part 2 (Analysis)")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
