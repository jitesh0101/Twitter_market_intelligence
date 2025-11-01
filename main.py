#!/usr/bin/env python3
"""
Main orchestrator for Twitter Market Intelligence System.
Complete pipeline from scraping to signal generation.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from src import (
    TwitterScraper,
    DataCleaner,
    Deduplicator,
    ParquetStorage,
    load_config,
    setup_logging,
)
from src.analyzer import TextProcessor, SignalGenerator, Visualizer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Twitter Market Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python main.py --all

  # Scrape only
  python main.py --scrape --target 500

  # Analyze existing data
  python main.py --analyze

  # Generate visualizations
  python main.py --visualize
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Run complete pipeline')
    parser.add_argument('--scrape', action='store_true', help='Scrape tweets')
    parser.add_argument('--process', action='store_true', help='Process data')
    parser.add_argument('--analyze', action='store_true', help='Analyze and generate signals')
    parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    parser.add_argument('--target', type=int, help='Target number of tweets')
    parser.add_argument('--hashtags', nargs='+', help='Hashtags to scrape')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    parser.add_argument('--output', default='data/analysis', help='Output directory')
    
    return parser.parse_args()


def run_scraping_pipeline(config, logger, target_tweets=None, hashtags=None):
    """Run scraping pipeline."""
    logger.info("=" * 70)
    logger.info("PHASE 1: WEB SCRAPING")
    logger.info("=" * 70)
    
    scraper_config = config.get_all()
    target = target_tweets or config.get("scraper", "target_tweets")
    tags = hashtags or config.get("scraper", "hashtags")
    
    try:
        scraper = TwitterScraper(scraper_config, logger)
        
        with scraper:
            tweets = scraper.scrape_hashtags(hashtags=tags, target_count=target)
        
        if tweets:
            storage = ParquetStorage(scraper_config, logger)
            storage.save_raw_tweets(tweets)
            logger.info(f"✓ Scraped {len(tweets)} tweets")
            return len(tweets)
        return 0
    except Exception as e:
        logger.error(f"Scraping error: {e}", exc_info=True)
        return 0


def run_processing_pipeline(config, logger):
    """Run processing pipeline."""
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 2: DATA PROCESSING")
    logger.info("=" * 70)
    
    try:
        storage = ParquetStorage(config.get_all(), logger)
        tweets_df = storage.load_raw_tweets()
        
        if len(tweets_df) == 0:
            logger.warning("No raw data found")
            return 0
        
        tweets = tweets_df.to_dict('records')
        
        cleaner = DataCleaner(config.get_all(), logger)
        cleaned_tweets = cleaner.clean_batch(tweets)
        
        deduplicator = Deduplicator(config.get_all(), logger)
        unique_tweets = deduplicator.deduplicate(cleaned_tweets)
        
        storage.save_processed_tweets(unique_tweets)
        logger.info(f"✓ Processed {len(unique_tweets)} unique tweets")
        return len(unique_tweets)
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        return 0


def run_analysis_pipeline(config, logger, output_dir):
    """Run analysis pipeline."""
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 3: NLP ANALYSIS & SIGNAL GENERATION")
    logger.info("=" * 70)
    
    try:
        storage = ParquetStorage(config.get_all(), logger)
        tweets_df = storage.load_processed_tweets()
        
        if len(tweets_df) == 0:
            logger.warning("No processed data found")
            return None, None, None
        
        # Feature extraction
        text_processor = TextProcessor(config.get_all(), logger)
        features_df = text_processor.process_tweets(tweets_df)
        
        # Signal generation
        signal_generator = SignalGenerator(config.get_all(), logger)
        signals_df = signal_generator.generate_signals(features_df)
        aggregated_df = signal_generator.aggregate_signals(signals_df, 'hashtags', min_tweets=3)
        report = signal_generator.generate_trading_report(signals_df)
        
        # Save results
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        storage.save_analysis_results(signals_df, 'signals_with_features.parquet')
        
        if len(aggregated_df) > 0:
            aggregated_df.to_parquet(output_path / 'aggregated_signals.parquet')
        
        with open(output_path / 'trading_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✓ Analysis complete. Results saved to {output_dir}")
        print_analysis_summary(report, logger)
        
        return signals_df, aggregated_df, report
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return None, None, None


def run_visualization_pipeline(config, logger, output_dir):
    """Run visualization pipeline."""
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 4: VISUALIZATION")
    logger.info("=" * 70)
    
    try:
        import pandas as pd
        from pathlib import Path
        
        # Load signals data directly with pandas
        signals_path = Path('data/analysis/signals_with_features.parquet')
        if not signals_path.exists():
            logger.warning("No analysis data found. Run analysis first: python main.py --analyze")
            return False
        
        signals_df = pd.read_parquet(signals_path)
        
        aggregated_path = Path('data/analysis/aggregated_signals.parquet')
        aggregated_df = pd.read_parquet(aggregated_path) if aggregated_path.exists() else pd.DataFrame()
        
        if len(signals_df) == 0:
            logger.warning("No analysis data found")
            return False
        
        visualizer = Visualizer(config.get_all(), logger)
        plot_dir = f"{output_dir}/plots"
        visualizer.generate_all_visualizations(signals_df, aggregated_df, plot_dir)
        
        logger.info(f"✓ Visualizations saved to {plot_dir}")
        return True
    except Exception as e:
        logger.error(f"Visualization error: {e}", exc_info=True)
        return False


def print_analysis_summary(report, logger):
    """Print analysis summary."""
    logger.info("\n" + "=" * 70)
    logger.info("ANALYSIS SUMMARY")
    logger.info("=" * 70)
    
    summary = report['summary']
    distribution = report['distribution']
    
    logger.info(f"Total Tweets: {summary['total_tweets']}")
    logger.info(f"Average Signal: {summary['avg_signal']:.3f}")
    logger.info(f"Market Sentiment: {summary['market_sentiment']}")
    logger.info(f"\nBullish: {distribution['bullish']} ({distribution['bullish_pct']:.1f}%)")
    logger.info(f"Bearish: {distribution['bearish']} ({distribution['bearish_pct']:.1f}%)")
    
    if report['top_hashtags']:
        logger.info("\nTop 5 Hashtags:")
        for i, (hashtag, data) in enumerate(list(report['top_hashtags'].items())[:5], 1):
            logger.info(f"  {i}. {hashtag}: {data['composite_signal_mean']:.3f} - {data['recommendation']}")


def main():
    """Main execution."""
    args = parse_arguments()
    
    try:
        config = load_config(args.config)
        logger = setup_logging(config.get_all())
    except Exception as e:
        print(f"Config error: {e}")
        return 1
    
    logger.info("=" * 70)
    logger.info("TWITTER MARKET INTELLIGENCE SYSTEM")
    logger.info("=" * 70)
    
    if not any([args.all, args.scrape, args.process, args.analyze, args.visualize]):
        logger.warning("No action specified. Use --all or specify phases")
        return 1
    
    try:
        if args.all or args.scrape:
            if run_scraping_pipeline(config, logger, args.target, args.hashtags) == 0:
                return 1
        
        if args.all or args.process:
            if run_processing_pipeline(config, logger) == 0:
                return 1
        
        if args.all or args.analyze:
            if run_analysis_pipeline(config, logger, args.output)[0] is None:
                return 1
        
        if args.all or args.visualize:
            run_visualization_pipeline(config, logger, args.output)
        
        logger.info("\n[SUCCESS] PIPELINE COMPLETE")
        return 0
    except KeyboardInterrupt:
        logger.warning("\nInterrupted")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
