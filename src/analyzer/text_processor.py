"""
Text processing and NLP analysis module.
Implements TF-IDF, feature extraction, and sentiment analysis.
"""

import re
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob

from ..utils import Logger


class TextProcessor:
    """Process tweet text for NLP analysis and feature extraction."""
    
    # Market-specific terms
    BULLISH_TERMS = {
        'bull', 'bullish', 'rally', 'surge', 'soar', 'gain', 'profit', 'high', 
        'breakout', 'uptrend', 'boom', 'growth', 'positive', 'strong', 'buy',
        'moon', 'rocket', 'pump', 'long', 'support', 'bounce', 'recovery'
    }
    
    BEARISH_TERMS = {
        'bear', 'bearish', 'crash', 'dump', 'fall', 'drop', 'loss', 'low',
        'breakdown', 'downtrend', 'decline', 'negative', 'weak', 'sell',
        'short', 'resistance', 'correction', 'panic', 'fear'
    }
    
    URGENCY_INDICATORS = {
        'urgent', 'now', 'immediately', 'breaking', 'alert', 'warning',
        'quick', 'fast', 'today', 'asap', 'hurry', 'rush'
    }
    
    # Price-related patterns
    PRICE_PATTERN = re.compile(r'₹?\s*\d+[,\d]*\.?\d*\s*(?:rs|inr|rupees)?', re.IGNORECASE)
    PERCENTAGE_PATTERN = re.compile(r'-?\d+\.?\d*\s*%')
    
    def __init__(self, config: dict, logger: Logger = None):
        """
        Initialize text processor.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or Logger.get_logger("TextProcessor")
        
        # Extract analysis configuration
        self.analysis_config = config.get("analysis", {})
        self.text_features_config = self.analysis_config.get("text_features", {})
        
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = None
        if self.text_features_config.get("use_tfidf", True):
            self._initialize_tfidf()
        
        self.logger.info("TextProcessor initialized")
    
    def _initialize_tfidf(self):
        """Initialize TF-IDF vectorizer."""
        max_features = self.text_features_config.get("max_features", 1000)
        ngram_range = tuple(self.text_features_config.get("ngram_range", [1, 2]))
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words='english',
            lowercase=True,
            strip_accents='unicode',
            token_pattern=r'\b[a-zA-Z]{2,}\b'
        )
        
        self.logger.info(f"TF-IDF initialized: max_features={max_features}, ngram_range={ngram_range}")
    
    def extract_sentiment(self, text: str) -> Dict[str, float]:
        """Extract sentiment from text using TextBlob."""
        try:
            blob = TextBlob(text)
            
            return {
                'polarity': blob.sentiment.polarity,  # -1 to 1
                'subjectivity': blob.sentiment.subjectivity,  # 0 to 1
                'sentiment_label': self._get_sentiment_label(blob.sentiment.polarity)
            }
        except Exception as e:
            self.logger.debug(f"Error extracting sentiment: {e}")
            return {'polarity': 0.0, 'subjectivity': 0.0, 'sentiment_label': 'neutral'}
    
    @staticmethod
    def _get_sentiment_label(polarity: float) -> str:
        """Convert polarity to label."""
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def extract_market_sentiment(self, text: str) -> Dict[str, any]:
        """Extract market-specific sentiment (bullish/bearish)."""
        text_lower = text.lower()
        words = set(text_lower.split())
        
        bullish_count = len(words.intersection(self.BULLISH_TERMS))
        bearish_count = len(words.intersection(self.BEARISH_TERMS))
        
        total = bullish_count + bearish_count
        if total > 0:
            bullish_ratio = bullish_count / total
            bearish_ratio = bearish_count / total
        else:
            bullish_ratio = 0.5
            bearish_ratio = 0.5
        
        if bullish_count > bearish_count:
            market_sentiment = 'bullish'
            confidence = bullish_ratio
        elif bearish_count > bullish_count:
            market_sentiment = 'bearish'
            confidence = bearish_ratio
        else:
            market_sentiment = 'neutral'
            confidence = 0.5
        
        return {
            'market_sentiment': market_sentiment,
            'bullish_score': bullish_ratio,
            'bearish_score': bearish_ratio,
            'confidence': confidence,
            'bullish_terms_count': bullish_count,
            'bearish_terms_count': bearish_count
        }
    
    def extract_urgency_score(self, text: str) -> float:
        """Calculate urgency score."""
        text_lower = text.lower()
        words = set(text_lower.split())
        
        urgency_count = len(words.intersection(self.URGENCY_INDICATORS))
        exclamation_count = text.count('!')
        
        urgency_score = min(1.0, (urgency_count * 0.2) + (exclamation_count * 0.1))
        return urgency_score
    
    def extract_price_mentions(self, text: str) -> Dict[str, any]:
        """Extract price and percentage mentions."""
        prices = self.PRICE_PATTERN.findall(text)
        percentages = self.PERCENTAGE_PATTERN.findall(text)
        
        return {
            'has_price': len(prices) > 0,
            'price_count': len(prices),
            'prices': prices,
            'has_percentage': len(percentages) > 0,
            'percentage_count': len(percentages),
            'percentages': percentages
        }
    
    def extract_all_features(self, text: str) -> Dict[str, any]:
        """Extract all text features from a tweet."""
        features = {}
        features.update(self.extract_sentiment(text))
        features.update(self.extract_market_sentiment(text))
        features['urgency_score'] = self.extract_urgency_score(text)
        features.update(self.extract_price_mentions(text))
        
        features['word_count'] = len(text.split())
        features['char_count'] = len(text)
        features['avg_word_length'] = features['char_count'] / features['word_count'] if features['word_count'] > 0 else 0
        
        return features
    
    def process_tweets(self, tweets: pd.DataFrame) -> pd.DataFrame:
        """Process a batch of tweets and extract features."""
        self.logger.info(f"Processing {len(tweets)} tweets for feature extraction...")
        
        features_list = []
        for idx, row in tweets.iterrows():
            text = row.get('content', '')
            features = self.extract_all_features(text)
            features_list.append(features)
        
        features_df = pd.DataFrame(features_list)
        result = pd.concat([tweets.reset_index(drop=True), features_df], axis=1)
        
        self.logger.info("Feature extraction complete")
        return result
    
    def fit_tfidf(self, texts: List[str]) -> TfidfVectorizer:
        """Fit TF-IDF vectorizer on texts."""
        if self.tfidf_vectorizer is None:
            self._initialize_tfidf()
        
        self.logger.info(f"Fitting TF-IDF on {len(texts)} documents...")
        self.tfidf_vectorizer.fit(texts)
        self.logger.info(f"TF-IDF fitted. Vocabulary size: {len(self.tfidf_vectorizer.vocabulary_)}")
        
        return self.tfidf_vectorizer
    
    def transform_tfidf(self, texts: List[str]) -> Tuple[np.ndarray, List[str]]:
        """Transform texts to TF-IDF features."""
        if self.tfidf_vectorizer is None:
            raise ValueError("TF-IDF vectorizer not fitted. Call fit_tfidf first.")
        
        tfidf_matrix = self.tfidf_vectorizer.transform(texts)
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        
        return tfidf_matrix, feature_names
    
    def get_top_terms(self, texts: List[str], top_n: int = 20) -> List[Tuple[str, float]]:
        """Get top terms by TF-IDF score."""
        if self.tfidf_vectorizer is None:
            self.fit_tfidf(texts)
        
        tfidf_matrix, feature_names = self.transform_tfidf(texts)
        mean_scores = tfidf_matrix.mean(axis=0).A1
        
        top_indices = mean_scores.argsort()[-top_n:][::-1]
        top_terms = [(feature_names[i], mean_scores[i]) for i in top_indices]
        
        return top_terms
