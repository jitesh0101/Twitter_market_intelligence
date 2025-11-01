"""
Visualization module for memory-efficient plotting.
Creates charts and graphs for signal analysis and market trends.
"""

from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for memory efficiency
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns

from ..utils import Logger


class Visualizer:
    """Create visualizations for tweet analysis and trading signals."""
    
    def __init__(self, config: dict, logger: Logger = None):
        """
        Initialize visualizer.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or Logger.get_logger("Visualizer")
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)
        plt.rcParams['font.size'] = 10
        
        self.logger.info("Visualizer initialized")
    
    def plot_sentiment_distribution(
        self,
        df: pd.DataFrame,
        output_path: Optional[str] = None,
        sample_size: int = 1000
    ):
        """
        Plot sentiment distribution.
        
        Args:
            df: DataFrame with sentiment data
            output_path: Path to save figure
            sample_size: Sample size for memory efficiency
        """
        # Sample if dataset is large
        if len(df) > sample_size:
            df_sample = df.sample(n=sample_size, random_state=42)
            self.logger.info(f"Sampling {sample_size} tweets for visualization")
        else:
            df_sample = df
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Polarity distribution
        axes[0].hist(df_sample['polarity'], bins=30, edgecolor='black', alpha=0.7)
        axes[0].set_xlabel('Polarity')
        axes[0].set_ylabel('Frequency')
        axes[0].set_title('Sentiment Polarity Distribution')
        axes[0].axvline(x=0, color='red', linestyle='--', linewidth=1)
        
        # Market sentiment
        market_sentiment_counts = df['market_sentiment'].value_counts()
        axes[1].bar(market_sentiment_counts.index, market_sentiment_counts.values, alpha=0.7)
        axes[1].set_xlabel('Market Sentiment')
        axes[1].set_ylabel('Count')
        axes[1].set_title('Market Sentiment Distribution')
        axes[1].tick_params(axis='x', rotation=45)
        
        # Sentiment label
        sentiment_counts = df['sentiment_label'].value_counts()
        axes[2].pie(
            sentiment_counts.values,
            labels=sentiment_counts.index,
            autopct='%1.1f%%',
            startangle=90
        )
        axes[2].set_title('Overall Sentiment')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            self.logger.info(f"Sentiment distribution saved to {output_path}")
        
        plt.close()
    
    def plot_signal_strength(
        self,
        df: pd.DataFrame,
        output_path: Optional[str] = None
    ):
        """
        Plot trading signal strength distribution.
        
        Args:
            df: DataFrame with signals
            output_path: Path to save figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Composite signal distribution
        axes[0, 0].hist(df['composite_signal'], bins=40, edgecolor='black', alpha=0.7, color='steelblue')
        axes[0, 0].set_xlabel('Composite Signal')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Composite Signal Distribution')
        axes[0, 0].axvline(x=0, color='red', linestyle='--', linewidth=2)
        
        # Signal strength
        axes[0, 1].hist(df['signal_strength'], bins=30, edgecolor='black', alpha=0.7, color='coral')
        axes[0, 1].set_xlabel('Signal Strength')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Signal Strength Distribution')
        
        # Signal direction
        signal_dir_counts = df['signal_direction'].value_counts()
        axes[1, 0].bar(signal_dir_counts.index, signal_dir_counts.values, alpha=0.7, color=['green', 'red'])
        axes[1, 0].set_xlabel('Signal Direction')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].set_title('Bullish vs Bearish Signals')
        
        # Scatter: engagement vs signal
        scatter_sample = df.sample(n=min(500, len(df)), random_state=42)
        axes[1, 1].scatter(
            scatter_sample['engagement_score'],
            scatter_sample['composite_signal'],
            alpha=0.5,
            c=scatter_sample['signal_strength'],
            cmap='viridis'
        )
        axes[1, 1].set_xlabel('Engagement Score')
        axes[1, 1].set_ylabel('Composite Signal')
        axes[1, 1].set_title('Engagement vs Signal')
        axes[1, 1].axhline(y=0, color='red', linestyle='--', linewidth=1)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            self.logger.info(f"Signal strength plot saved to {output_path}")
        
        plt.close()
    
    def plot_time_series(
        self,
        df: pd.DataFrame,
        output_path: Optional[str] = None,
        resample_freq: str = '1H'
    ):
        """
        Plot time series of signals.
        
        Args:
            df: DataFrame with signals and timestamps
            output_path: Path to save figure
            resample_freq: Resampling frequency
        """
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Resample for memory efficiency
        df_resampled = df.set_index('timestamp').resample(resample_freq).agg({
            'composite_signal': 'mean',
            'engagement_score': 'mean',
            'urgency_signal': 'mean',
            'polarity': 'mean'
        }).reset_index()
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))
        
        # Composite signal over time
        axes[0].plot(df_resampled['timestamp'], df_resampled['composite_signal'], linewidth=2, color='blue')
        axes[0].fill_between(
            df_resampled['timestamp'],
            df_resampled['composite_signal'],
            0,
            where=(df_resampled['composite_signal'] > 0),
            alpha=0.3,
            color='green',
            label='Bullish'
        )
        axes[0].fill_between(
            df_resampled['timestamp'],
            df_resampled['composite_signal'],
            0,
            where=(df_resampled['composite_signal'] < 0),
            alpha=0.3,
            color='red',
            label='Bearish'
        )
        axes[0].axhline(y=0, color='black', linestyle='--', linewidth=1)
        axes[0].set_xlabel('Time')
        axes[0].set_ylabel('Composite Signal')
        axes[0].set_title('Trading Signal Over Time')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Multiple signals
        axes[1].plot(df_resampled['timestamp'], df_resampled['polarity'], label='Sentiment', linewidth=2)
        axes[1].plot(df_resampled['timestamp'], df_resampled['engagement_score'], label='Engagement', linewidth=2)
        axes[1].plot(df_resampled['timestamp'], df_resampled['urgency_signal'], label='Urgency', linewidth=2)
        axes[1].set_xlabel('Time')
        axes[1].set_ylabel('Score')
        axes[1].set_title('Signal Components Over Time')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            self.logger.info(f"Time series plot saved to {output_path}")
        
        plt.close()
    
    def plot_hashtag_signals(
        self,
        aggregated_df: pd.DataFrame,
        output_path: Optional[str] = None,
        top_n: int = 10
    ):
        """
        Plot signals by hashtag.
        
        Args:
            aggregated_df: Aggregated signals by hashtag
            output_path: Path to save figure
            top_n: Number of top hashtags to show
        """
        # Get top hashtags
        top_hashtags = aggregated_df.head(top_n)
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        # Bar chart of signals
        colors = ['green' if x > 0 else 'red' for x in top_hashtags['composite_signal_mean']]
        axes[0].barh(range(len(top_hashtags)), top_hashtags['composite_signal_mean'], color=colors, alpha=0.7)
        axes[0].set_yticks(range(len(top_hashtags)))
        axes[0].set_yticklabels(top_hashtags.index)
        axes[0].set_xlabel('Average Composite Signal')
        axes[0].set_title(f'Top {top_n} Hashtags by Signal')
        axes[0].axvline(x=0, color='black', linestyle='--', linewidth=1)
        axes[0].invert_yaxis()
        
        # Signal strength with confidence
        x = range(len(top_hashtags))
        axes[1].scatter(
            top_hashtags['composite_signal_mean'],
            top_hashtags['aggregate_confidence'],
            s=top_hashtags['composite_signal_count'] * 10,
            alpha=0.6,
            c=colors
        )
        
        for i, hashtag in enumerate(top_hashtags.index):
            axes[1].annotate(
                hashtag,
                (top_hashtags['composite_signal_mean'].iloc[i], top_hashtags['aggregate_confidence'].iloc[i]),
                fontsize=8,
                alpha=0.7
            )
        
        axes[1].set_xlabel('Average Signal')
        axes[1].set_ylabel('Confidence')
        axes[1].set_title('Signal vs Confidence (size = tweet count)')
        axes[1].axvline(x=0, color='black', linestyle='--', linewidth=1)
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            self.logger.info(f"Hashtag signals plot saved to {output_path}")
        
        plt.close()
    
    def create_interactive_dashboard(
        self,
        df: pd.DataFrame,
        output_path: Optional[str] = None
    ):
        """
        Create interactive Plotly dashboard.
        
        Args:
            df: DataFrame with signals
            output_path: Path to save HTML file
        """
        # Sample for performance
        df_sample = df.sample(n=min(1000, len(df)), random_state=42)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Signal Distribution',
                'Market Sentiment',
                'Engagement vs Signal',
                'Signal Strength Over Time'
            ),
            specs=[
                [{'type': 'histogram'}, {'type': 'bar'}],
                [{'type': 'scatter'}, {'type': 'scatter'}]
            ]
        )
        
        # Signal distribution
        fig.add_trace(
            go.Histogram(x=df['composite_signal'], name='Signal', marker_color='steelblue'),
            row=1, col=1
        )
        
        # Market sentiment
        sentiment_counts = df['market_sentiment'].value_counts()
        fig.add_trace(
            go.Bar(x=sentiment_counts.index, y=sentiment_counts.values, name='Sentiment'),
            row=1, col=2
        )
        
        # Engagement vs Signal
        fig.add_trace(
            go.Scatter(
                x=df_sample['engagement_score'],
                y=df_sample['composite_signal'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=df_sample['signal_strength'],
                    colorscale='Viridis',
                    showscale=True
                ),
                text=df_sample['content'].str[:100],
                name='Tweets'
            ),
            row=2, col=1
        )
        
        # Time series
        df_sorted = df.sort_values('timestamp')
        fig.add_trace(
            go.Scatter(
                x=df_sorted['timestamp'],
                y=df_sorted['composite_signal'].rolling(window=50).mean(),
                mode='lines',
                name='Signal (MA50)',
                line=dict(color='blue', width=2)
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Twitter Market Intelligence Dashboard"
        )
        
        if output_path:
            fig.write_html(output_path)
            self.logger.info(f"Interactive dashboard saved to {output_path}")
        
        return fig
    
    def generate_all_visualizations(
        self,
        df: pd.DataFrame,
        aggregated_df: pd.DataFrame,
        output_dir: str = "data/analysis/plots"
    ):
        """
        Generate all visualizations.
        
        Args:
            df: DataFrame with signals
            aggregated_df: Aggregated signals
            output_dir: Output directory for plots
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Generating all visualizations...")
        
        # Static plots
        self.plot_sentiment_distribution(df, output_path / "sentiment_distribution.png")
        self.plot_signal_strength(df, output_path / "signal_strength.png")
        self.plot_time_series(df, output_path / "time_series.png")
        
        if len(aggregated_df) > 0:
            self.plot_hashtag_signals(aggregated_df, output_path / "hashtag_signals.png")
        
        # Interactive dashboard
        self.create_interactive_dashboard(df, output_path / "dashboard.html")
        
        self.logger.info(f"All visualizations saved to {output_dir}")
