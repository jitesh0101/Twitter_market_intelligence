#!/usr/bin/env python3
"""
Standalone analysis script for processed tweet data.
Performs NLP analysis and generates trading signals.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from src import load_config, setup_logging, ParquetStorage
from src.analyzer import TextProcessor, SignalGenerator


def main():
    parser = argparse.ArgumentParser(description="Analyze tweets and generate signals")
    parser.add_argument('--input', default='data/processed/tweets_processed.parquet', help='Input parquet file')
    parser.add_argument('--output', default='data/analysis', help='Output directory')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    args = parser.parse_args()
    
    # Setup
    config = load_config(args.config)
    logger = setup_logging(config.get_all())
    
    logger.info("=" * 70)
    logger.info("TWITTER ANALYSIS & SIGNAL GENERATION")
    logger.info("=" * 70)
    
    # Load data
    logger.info(f"Loading data from {args.input}...")
    tweets_df = pd.read_parquet(args.input)
    logger.info(f"Loaded {len(tweets_df)} tweets")
    
    # Feature extraction
    logger.info("\nExtracting features...")
    text_processor = TextProcessor(config.get_all(), logger)
    features_df = text_processor.process_tweets(tweets_df)
    
    # Get top terms
    texts = features_df['content'].tolist()
    top_terms = text_processor.get_top_terms(texts, top_n=20)
    logger.info("\nTop 20 Terms by TF-IDF:")
    for i, (term, score) in enumerate(top_terms, 1):
        logger.info(f"  {i}. {term}: {score:.4f}")
    
    # Generate signals
    logger.info("\nGenerating trading signals...")
    signal_generator = SignalGenerator(config.get_all(), logger)
    signals_df = signal_generator.generate_signals(features_df)
    
    # Aggregate by hashtag
    logger.info("\nAggregating signals by hashtag...")
    aggregated_df = signal_generator.aggregate_signals(signals_df, 'hashtags', min_tweets=3)
    
    # Generate report
    logger.info("\nGenerating trading report...")
    report = signal_generator.generate_trading_report(signals_df)
    
    # Save results
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    signals_df.to_parquet(output_path / 'signals_with_features.parquet', index=False)
    logger.info(f"Saved signals to {output_path / 'signals_with_features.parquet'}")
    
    if len(aggregated_df) > 0:
        aggregated_df.to_parquet(output_path / 'aggregated_signals.parquet')
        logger.info(f"Saved aggregated signals to {output_path / 'aggregated_signals.parquet'}")
        
        logger.info("\nTop Hashtags by Signal:")
        print(aggregated_df.head(10))
    
    with open(output_path / 'trading_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved report to {output_path / 'trading_report.json'}")
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total Tweets: {report['summary']['total_tweets']}")
    logger.info(f"Market Sentiment: {report['summary']['market_sentiment']}")
    logger.info(f"Average Signal: {report['summary']['avg_signal']:.3f}")
    logger.info(f"Bullish: {report['distribution']['bullish_pct']:.1f}%")
    logger.info(f"Bearish: {report['distribution']['bearish_pct']:.1f}%")
    
    logger.info("\n Analysis complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
