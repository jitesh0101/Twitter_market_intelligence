"""
Sample test file for Twitter Market Intelligence System.
Run with: pytest tests/test_sample.py
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

# Test imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.processor.data_cleaner import DataCleaner
from src.processor.deduplicator import Deduplicator
from src.analyzer.text_processor import TextProcessor
from src.analyzer.signal_generator import SignalGenerator


# Fixtures
@pytest.fixture
def sample_tweets():
    """Create sample tweet data for testing."""
    return pd.DataFrame({
        'tweet_id': ['1', '2', '3', '4', '5'],
        'username': ['user1', 'user2', 'user3', 'user4', 'user5'],
        'content': [
            'NIFTY50 looking bullish! Target 20000. #nifty50 #bullish',
            'Market crash incoming. Sell everything. #bearish #sensex',
            'Great support at 19500. Buy the dip! #intraday',
            'NIFTY50 looking bullish! Target 20000. #nifty50 #bullish',  # Duplicate
            'Neutral market. Wait for clear signals. #trading'
        ],
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='H'),
        'replies': [10, 5, 15, 10, 3],
        'retweets': [20, 8, 25, 20, 5],
        'likes': [50, 30, 60, 50, 10],
        'views': [1000, 500, 1500, 1000, 200],
        'mentions': [['user2'], [], ['user1'], ['user2'], []],
        'hashtags': [['nifty50', 'bullish'], ['bearish', 'sensex'], 
                     ['intraday'], ['nifty50', 'bullish'], ['trading']]
    })


# Data Cleaner Tests
class TestDataCleaner:
    
    def test_clean_text_removes_urls(self):
        """Test that URLs are removed from text."""
        cleaner = DataCleaner()
        text = "Check this out https://example.com #bullish"
        cleaned = cleaner.clean_text(text)
        assert 'https://example.com' not in cleaned
        assert '#bullish' in cleaned
    
    def test_clean_text_normalizes_unicode(self):
        """Test Unicode normalization."""
        cleaner = DataCleaner()
        text = "café résumé"
        cleaned = cleaner.clean_text(text)
        assert cleaned is not None
        assert len(cleaned) > 0
    
    def test_clean_dataframe(self, sample_tweets):
        """Test DataFrame cleaning."""
        cleaner = DataCleaner()
        df_clean = cleaner.clean_dataframe(sample_tweets)
        
        assert 'content_cleaned' in df_clean.columns
        assert len(df_clean) <= len(sample_tweets)
        assert df_clean['content_cleaned'].notna().all()


# Deduplicator Tests
class TestDeduplicator:
    
    def test_deduplicate_by_content_hash(self, sample_tweets):
        """Test content hash deduplication."""
        dedup = Deduplicator()
        df_unique = dedup.deduplicate_by_content_hash(sample_tweets)
        
        # Should remove the duplicate tweet (index 3 is duplicate of 0)
        assert len(df_unique) == 4
    
    def test_generate_content_hash(self):
        """Test content hash generation."""
        dedup = Deduplicator()
        hash1 = dedup.generate_content_hash("Hello World")
        hash2 = dedup.generate_content_hash("hello world")
        hash3 = dedup.generate_content_hash("Different")
        
        # Same content (case-insensitive) should have same hash
        assert hash1 == hash2
        # Different content should have different hash
        assert hash1 != hash3
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        dedup = Deduplicator()
        
        sim1 = dedup.calculate_similarity("Hello World", "Hello World")
        assert sim1 == 1.0
        
        sim2 = dedup.calculate_similarity("Hello", "World")
        assert 0 < sim2 < 1
        
        sim3 = dedup.calculate_similarity("NIFTY bullish", "NIFTY is bullish today")
        assert sim3 > 0.5  # Should be similar


# Text Processor Tests
class TestTextProcessor:
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis."""
        processor = TextProcessor()
        
        # Positive sentiment
        pos_result = processor.analyze_sentiment("Great market! Bullish trend!")
        assert pos_result['compound'] > 0
        
        # Negative sentiment
        neg_result = processor.analyze_sentiment("Terrible market crash!")
        assert neg_result['compound'] < 0
        
        # Neutral sentiment
        neu_result = processor.analyze_sentiment("The market is open today.")
        assert abs(neu_result['compound']) < 0.3
    
    def test_extract_market_sentiment(self):
        """Test market-specific sentiment extraction."""
        processor = TextProcessor()
        
        # Bullish content
        bull_result = processor.extract_market_sentiment("Buy now! Breakout rally expected!")
        assert bull_result['bullish_count'] > 0
        assert bull_result['market_sentiment'] > 0
        
        # Bearish content
        bear_result = processor.extract_market_sentiment("Sell everything! Market will crash!")
        assert bear_result['bearish_count'] > 0
        assert bear_result['market_sentiment'] < 0
    
    def test_process_dataframe(self, sample_tweets):
        """Test DataFrame processing."""
        processor = TextProcessor()
        df_processed = processor.process_dataframe(sample_tweets)
        
        # Check new columns added
        assert 'compound' in df_processed.columns
        assert 'polarity' in df_processed.columns
        assert 'market_sentiment' in df_processed.columns
        assert 'bullish_count' in df_processed.columns
        assert 'bearish_count' in df_processed.columns


# Signal Generator Tests
class TestSignalGenerator:
    
    def test_normalize_engagement(self, sample_tweets):
        """Test engagement normalization."""
        signal_gen = SignalGenerator()
        df_norm = signal_gen.normalize_engagement(sample_tweets)
        
        assert 'total_engagement' in df_norm.columns
        assert 'engagement_normalized' in df_norm.columns
        assert df_norm['engagement_normalized'].between(0, 1).all()
    
    def test_calculate_sentiment_signal(self):
        """Test sentiment signal calculation."""
        signal_gen = SignalGenerator()
        
        # Mock row with sentiment data
        row = pd.Series({
            'compound': 0.8,
            'market_sentiment': 0.6
        })
        
        signal = signal_gen.calculate_sentiment_signal(row)
        assert -1 <= signal <= 1
        assert signal > 0  # Should be positive
    
    def test_generate_signals(self, sample_tweets):
        """Test signal generation."""
        # First process with text processor
        processor = TextProcessor()
        df_processed = processor.process_dataframe(sample_tweets)
        
        # Then generate signals
        signal_gen = SignalGenerator()
        df_signals = signal_gen.generate_signals(df_processed)
        
        # Check signal columns added
        assert 'signal' in df_signals.columns
        assert 'signal_confidence' in df_signals.columns
        assert 'signal_direction' in df_signals.columns
        assert 'signal_strength' in df_signals.columns
        
        # Check value ranges
        assert df_signals['signal'].between(-1, 1).all()
        assert df_signals['signal_confidence'].between(0, 1).all()
        assert df_signals['signal_direction'].isin(['BULLISH', 'BEARISH', 'NEUTRAL']).all()
    
    def test_get_top_signals(self, sample_tweets):
        """Test getting top signals."""
        # Process and generate signals
        processor = TextProcessor()
        df_processed = processor.process_dataframe(sample_tweets)
        signal_gen = SignalGenerator()
        df_signals = signal_gen.generate_signals(df_processed)
        
        # Get top signals
        top_signals = signal_gen.get_top_signals(df_signals, n=3, min_confidence=0.0)
        
        assert len(top_signals) <= 3
        assert all(col in top_signals.columns for col in ['signal', 'signal_confidence'])


# Integration Tests
class TestIntegration:
    
    def test_full_pipeline(self, sample_tweets):
        """Test complete processing pipeline."""
        # Clean
        cleaner = DataCleaner()
        df_clean = cleaner.clean_dataframe(sample_tweets)
        
        # Deduplicate
        dedup = Deduplicator()
        df_unique = dedup.deduplicate(df_clean)
        
        # Process text
        processor = TextProcessor()
        df_processed = processor.process_dataframe(df_unique)
        
        # Generate signals
        signal_gen = SignalGenerator()
        df_final = signal_gen.generate_signals(df_processed)
        
        # Verify final output
        assert len(df_final) > 0
        assert 'signal' in df_final.columns
        assert 'signal_confidence' in df_final.columns
        assert df_final['signal'].notna().all()


# Performance Tests
class TestPerformance:
    
    def test_processing_speed(self):
        """Test that processing completes in reasonable time."""
        import time
        
        # Create larger dataset
        n = 1000
        df = pd.DataFrame({
            'tweet_id': [str(i) for i in range(n)],
            'username': [f'user{i}' for i in range(n)],
            'content': ['Sample tweet about market #trading'] * n,
            'timestamp': pd.date_range('2024-01-01', periods=n, freq='min'),
            'replies': np.random.randint(0, 100, n),
            'retweets': np.random.randint(0, 100, n),
            'likes': np.random.randint(0, 1000, n),
            'views': np.random.randint(0, 10000, n),
            'mentions': [[] for _ in range(n)],
            'hashtags': [['trading'] for _ in range(n)]
        })
        
        # Time the processing
        start = time.time()
        
        cleaner = DataCleaner()
        df_clean = cleaner.clean_dataframe(df)
        
        processor = TextProcessor()
        df_processed = processor.process_dataframe(df_clean)
        
        signal_gen = SignalGenerator()
        df_final = signal_gen.generate_signals(df_processed)
        
        elapsed = time.time() - start
        
        # Should process 1000 tweets in under 10 seconds
        assert elapsed < 10, f"Processing took {elapsed:.2f}s, expected < 10s"
        assert len(df_final) == n


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
