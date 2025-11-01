"""
Signal generation module for algorithmic trading.
Converts text features into quantitative trading signals with confidence intervals.
"""

from typing import Dict, Tuple

import numpy as np
import pandas as pd

from ..utils import Logger


class SignalGenerator:
    """Generate trading signals from tweet features."""
    
    def __init__(self, config: dict, logger: Logger = None):
        """
        Initialize signal generator.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or Logger.get_logger("SignalGenerator")
        
        # Extract signal configuration
        self.analysis_config = config.get("analysis", {})
        self.signal_weights = self.analysis_config.get("signal_weights", {
            'sentiment': 0.3,
            'engagement': 0.3,
            'urgency': 0.2,
            'technical_terms': 0.2
        })
        
        self.logger.info(f"SignalGenerator initialized with weights: {self.signal_weights}")
    
    def calculate_engagement_score(self, row: pd.Series) -> float:
        """
        Calculate engagement score from metrics.
        
        Args:
            row: DataFrame row with engagement metrics
            
        Returns:
            Normalized engagement score (0 to 1)
        """
        likes = row.get('likes', 0)
        retweets = row.get('retweets', 0)
        replies = row.get('replies', 0)
        
        # Weighted engagement score
        engagement = (likes * 1.0) + (retweets * 2.0) + (replies * 1.5)
        
        # Normalize using log scale to handle outliers
        if engagement > 0:
            normalized = min(1.0, np.log1p(engagement) / 10.0)
        else:
            normalized = 0.0
        
        return normalized
    
    def calculate_sentiment_signal(self, row: pd.Series) -> float:
        """
        Calculate sentiment signal (-1 to 1).
        
        Args:
            row: DataFrame row with sentiment features
            
        Returns:
            Sentiment signal
        """
        # Combine general sentiment and market sentiment
        polarity = row.get('polarity', 0.0)
        bullish_score = row.get('bullish_score', 0.5)
        bearish_score = row.get('bearish_score', 0.5)
        
        # Market sentiment signal (-1 for bearish, 1 for bullish)
        market_signal = bullish_score - bearish_score
        
        # Combined signal (weighted average)
        sentiment_signal = (polarity * 0.4) + (market_signal * 0.6)
        
        return np.clip(sentiment_signal, -1, 1)
    
    def calculate_urgency_signal(self, row: pd.Series) -> float:
        """
        Calculate urgency signal (0 to 1).
        
        Args:
            row: DataFrame row with urgency features
            
        Returns:
            Urgency signal
        """
        return row.get('urgency_score', 0.0)
    
    def calculate_technical_signal(self, row: pd.Series) -> float:
        """
        Calculate technical terms signal (0 to 1).
        
        Args:
            row: DataFrame row with features
            
        Returns:
            Technical signal based on market terms
        """
        bullish_count = row.get('bullish_terms_count', 0)
        bearish_count = row.get('bearish_terms_count', 0)
        has_price = row.get('has_price', False)
        has_percentage = row.get('has_percentage', False)
        
        # Base signal from term counts
        total_terms = bullish_count + bearish_count
        if total_terms > 0:
            signal = bullish_count / total_terms
        else:
            signal = 0.5
        
        # Boost if has price/percentage mentions
        if has_price or has_percentage:
            signal = min(1.0, signal * 1.2)
        
        return signal
    
    def calculate_composite_signal(self, row: pd.Series) -> Dict[str, float]:
        """
        Calculate composite trading signal from all features.
        
        Args:
            row: DataFrame row with all features
            
        Returns:
            Dictionary with signal components and composite signal
        """
        # Calculate component signals
        sentiment_signal = self.calculate_sentiment_signal(row)
        engagement_score = self.calculate_engagement_score(row)
        urgency_signal = self.calculate_urgency_signal(row)
        technical_signal = self.calculate_technical_signal(row)
        
        # Composite signal (weighted combination)
        composite = (
            sentiment_signal * self.signal_weights.get('sentiment', 0.3) +
            engagement_score * self.signal_weights.get('engagement', 0.3) +
            urgency_signal * self.signal_weights.get('urgency', 0.2) +
            technical_signal * self.signal_weights.get('technical_terms', 0.2)
        )
        
        # Normalize to -1 to 1 range (bearish to bullish)
        # Convert from 0-1 to -1 to 1
        composite_normalized = (composite * 2) - 1
        
        return {
            'sentiment_signal': sentiment_signal,
            'engagement_score': engagement_score,
            'urgency_signal': urgency_signal,
            'technical_signal': technical_signal,
            'composite_signal': composite_normalized,
            'signal_strength': abs(composite_normalized),
            'signal_direction': 'bullish' if composite_normalized > 0 else 'bearish'
        }
    
    def calculate_confidence_interval(
        self,
        signal: float,
        row: pd.Series,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for signal.
        
        Args:
            signal: Signal value
            row: DataFrame row with features
            confidence_level: Confidence level (default 0.95)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Factors that affect confidence
        engagement = self.calculate_engagement_score(row)
        subjectivity = row.get('subjectivity', 0.5)
        market_confidence = row.get('confidence', 0.5)
        
        # Calculate uncertainty (inverse of confidence)
        # Higher engagement = lower uncertainty
        # Lower subjectivity = lower uncertainty
        # Higher market confidence = lower uncertainty
        uncertainty = (
            (1 - engagement) * 0.4 +
            subjectivity * 0.3 +
            (1 - market_confidence) * 0.3
        )
        
        # Calculate margin of error
        # Z-score for 95% confidence ≈ 1.96
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 99%
        margin = z_score * uncertainty * 0.5  # Scale down
        
        lower = np.clip(signal - margin, -1, 1)
        upper = np.clip(signal + margin, -1, 1)
        
        return (lower, upper)
    
    def generate_signals(self, tweets_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals for all tweets.
        
        Args:
            tweets_df: DataFrame with processed tweets
            
        Returns:
            DataFrame with generated signals
        """
        self.logger.info(f"Generating signals for {len(tweets_df)} tweets...")
        
        signals_list = []
        
        for idx, row in tweets_df.iterrows():
            # Calculate composite signal
            signals = self.calculate_composite_signal(row)
            
            # Calculate confidence interval
            lower, upper = self.calculate_confidence_interval(
                signals['composite_signal'],
                row
            )
            signals['confidence_lower'] = lower
            signals['confidence_upper'] = upper
            signals['confidence_width'] = upper - lower
            
            signals_list.append(signals)
        
        # Create signals DataFrame
        signals_df = pd.DataFrame(signals_list)
        
        # Combine with original data
        result = pd.concat([tweets_df.reset_index(drop=True), signals_df], axis=1)
        
        self.logger.info("Signal generation complete")
        return result
    
    def aggregate_signals(
        self,
        signals_df: pd.DataFrame,
        groupby: str = 'hashtags',
        min_tweets: int = 5
    ) -> pd.DataFrame:
        """
        Aggregate signals by category (hashtag, time period, etc.).
        
        Args:
            signals_df: DataFrame with signals
            groupby: Column to group by
            min_tweets: Minimum tweets required for aggregation
            
        Returns:
            Aggregated signals DataFrame
        """
        self.logger.info(f"Aggregating signals by {groupby}...")
        
        if groupby == 'hashtags':
            # Explode hashtags (one row per hashtag)
            exploded = signals_df.explode('hashtags')
            groupby_col = 'hashtags'
        else:
            exploded = signals_df
            groupby_col = groupby
        
        # Group and aggregate
        agg_dict = {
            'composite_signal': ['mean', 'std', 'count'],
            'sentiment_signal': 'mean',
            'engagement_score': 'mean',
            'urgency_signal': 'mean',
            'signal_strength': 'mean',
            'confidence_width': 'mean'
        }
        
        aggregated = exploded.groupby(groupby_col).agg(agg_dict)
        aggregated.columns = ['_'.join(col).strip() for col in aggregated.columns.values]
        
        # Filter by minimum tweets
        aggregated = aggregated[aggregated['composite_signal_count'] >= min_tweets]
        
        # Calculate aggregate confidence
        aggregated['aggregate_confidence'] = 1 - (aggregated['confidence_width_mean'] / 2)
        
        # Determine recommendation
        def get_recommendation(row):
            signal = row['composite_signal_mean']
            strength = abs(signal)
            confidence = row['aggregate_confidence']
            
            if strength > 0.3 and confidence > 0.6:
                if signal > 0:
                    return 'STRONG BUY' if strength > 0.6 else 'BUY'
                else:
                    return 'STRONG SELL' if strength > 0.6 else 'SELL'
            else:
                return 'HOLD'
        
        aggregated['recommendation'] = aggregated.apply(get_recommendation, axis=1)
        
        # Sort by signal strength
        aggregated = aggregated.sort_values('composite_signal_mean', ascending=False)
        
        self.logger.info(f"Aggregated {len(aggregated)} groups")
        return aggregated
    
    def generate_trading_report(self, signals_df: pd.DataFrame) -> Dict[str, any]:
        """
        Generate trading report with actionable insights.
        
        Args:
            signals_df: DataFrame with signals
            
        Returns:
            Dictionary with report data
        """
        self.logger.info("Generating trading report...")
        
        # Overall market sentiment
        avg_signal = signals_df['composite_signal'].mean()
        signal_std = signals_df['composite_signal'].std()
        
        # Distribution
        bullish_count = len(signals_df[signals_df['composite_signal'] > 0.2])
        bearish_count = len(signals_df[signals_df['composite_signal'] < -0.2])
        neutral_count = len(signals_df) - bullish_count - bearish_count
        
        # Strong signals
        strong_bullish = signals_df[
            (signals_df['composite_signal'] > 0.5) &
            (signals_df['signal_strength'] > 0.5)
        ]
        strong_bearish = signals_df[
            (signals_df['composite_signal'] < -0.5) &
            (signals_df['signal_strength'] > 0.5)
        ]
        
        # Top hashtags
        hashtag_signals = self.aggregate_signals(signals_df, 'hashtags', min_tweets=3)
        
        report = {
            'summary': {
                'total_tweets': len(signals_df),
                'avg_signal': float(avg_signal),
                'signal_std': float(signal_std),
                'market_sentiment': 'BULLISH' if avg_signal > 0.1 else 'BEARISH' if avg_signal < -0.1 else 'NEUTRAL'
            },
            'distribution': {
                'bullish': int(bullish_count),
                'bearish': int(bearish_count),
                'neutral': int(neutral_count),
                'bullish_pct': float(bullish_count / len(signals_df) * 100),
                'bearish_pct': float(bearish_count / len(signals_df) * 100)
            },
            'strong_signals': {
                'strong_bullish_count': len(strong_bullish),
                'strong_bearish_count': len(strong_bearish)
            },
            'top_hashtags': hashtag_signals.head(10).to_dict('index') if len(hashtag_signals) > 0 else {}
        }
        
        self.logger.info("Trading report generated")
        return report
