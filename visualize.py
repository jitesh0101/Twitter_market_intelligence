#!/usr/bin/env python3
"""
Standalone visualization script for signal analysis.
Generates charts, graphs, and interactive dashboards.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from src import load_config, setup_logging
from src.analyzer import Visualizer


def main():
    parser = argparse.ArgumentParser(description="Generate visualizations for signal analysis")
    parser.add_argument('--input', default='data/analysis/signals_with_features.parquet', help='Input signals file')
    parser.add_argument('--aggregated', default='data/analysis/aggregated_signals.parquet', help='Aggregated signals file')
    parser.add_argument('--output', default='data/analysis/plots', help='Output directory')
    parser.add_argument('--config', default='config.yaml', help='Config file')
    parser.add_argument('--format', choices=['all', 'static', 'interactive'], default='all', help='Visualization format')
    args = parser.parse_args()
    
    # Setup
    config = load_config(args.config)
    logger = setup_logging(config.get_all())
    
    logger.info("=" * 70)
    logger.info("VISUALIZATION GENERATION")
    logger.info("=" * 70)
    
    # Load data
    logger.info(f"Loading signals from {args.input}...")
    signals_df = pd.read_parquet(args.input)
    logger.info(f"Loaded {len(signals_df)} signals")
    
    # Load aggregated data if available
    aggregated_path = Path(args.aggregated)
    if aggregated_path.exists():
        logger.info(f"Loading aggregated signals from {args.aggregated}...")
        aggregated_df = pd.read_parquet(aggregated_path)
        logger.info(f"Loaded {len(aggregated_df)} aggregated signals")
    else:
        logger.warning("Aggregated signals not found, skipping hashtag visualizations")
        aggregated_df = pd.DataFrame()
    
    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize visualizer
    visualizer = Visualizer(config.get_all(), logger)
    
    # Generate visualizations based on format
    if args.format in ['all', 'static']:
        logger.info("\nGenerating static visualizations...")
        
        visualizer.plot_sentiment_distribution(signals_df, output_path / "sentiment_distribution.png")
        visualizer.plot_signal_strength(signals_df, output_path / "signal_strength.png")
        visualizer.plot_time_series(signals_df, output_path / "time_series.png")
        
        if len(aggregated_df) > 0:
            visualizer.plot_hashtag_signals(aggregated_df, output_path / "hashtag_signals.png")
        
        logger.info(f" Static plots saved to {output_path}")
    
    if args.format in ['all', 'interactive']:
        logger.info("\nGenerating interactive dashboard...")
        
        visualizer.create_interactive_dashboard(signals_df, output_path / "dashboard.html")
        
        logger.info(f" Interactive dashboard saved to {output_path / 'dashboard.html'}")
    
    logger.info("\n" + "=" * 70)
    logger.info("VISUALIZATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Output directory: {output_path}")
    logger.info("\nGenerated files:")
    
    for file in output_path.glob("*"):
        if file.is_file():
            logger.info(f"  - {file.name}")
    
    logger.info("\n All visualizations generated successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
