"""
Data cleaning and normalization module.
Handles text cleaning, Unicode processing, and data validation.
"""

import re
from typing import Dict, List
import unicodedata

from ..utils import Logger, is_valid_tweet_content


class DataCleaner:
    """Clean and normalize tweet data."""
    
    # URL pattern
    URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    
    # Mention pattern (@username)
    MENTION_PATTERN = re.compile(r'@[\w]+')
    
    # Hashtag pattern (#hashtag)
    HASHTAG_PATTERN = re.compile(r'#[\w]+')
    
    # Extra whitespace pattern
    WHITESPACE_PATTERN = re.compile(r'\s+')
    
    def __init__(self, config: dict, logger: Logger = None):
        """
        Initialize data cleaner.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or Logger.get_logger("DataCleaner")
        
        # Extract cleaning configuration
        self.cleaning_config = config.get("processor", {}).get("cleaning", {})
        self.normalization_config = config.get("processor", {}).get("normalization", {})
        
        self.logger.info("DataCleaner initialized")
    
    def clean_tweet(self, tweet: Dict) -> Dict:
        """
        Clean a single tweet.
        
        Args:
            tweet: Tweet dictionary
            
        Returns:
            Cleaned tweet dictionary
        """
        cleaned = tweet.copy()
        
        # Clean content
        if 'content' in cleaned:
            cleaned['content'] = self.clean_text(cleaned['content'])
            cleaned['content_length'] = len(cleaned['content'])
        
        # Handle Unicode
        if self.cleaning_config.get("handle_unicode", True):
            cleaned = self._handle_unicode(cleaned)
        
        # Validate content length
        min_length = self.cleaning_config.get("min_content_length", 10)
        if cleaned.get('content_length', 0) < min_length:
            cleaned['is_valid'] = False
        else:
            cleaned['is_valid'] = True
        
        return cleaned
    
    def clean_text(self, text: str) -> str:
        """
        Clean tweet text content.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        cleaned = text
        
        # Remove URLs if configured
        if self.normalization_config.get("remove_urls", True):
            cleaned = self.URL_PATTERN.sub('', cleaned)
        
        # Remove mentions if configured
        if self.normalization_config.get("remove_mentions", False):
            cleaned = self.MENTION_PATTERN.sub('', cleaned)
        
        # Remove hashtags if configured
        if self.normalization_config.get("remove_hashtags", False):
            cleaned = self.HASHTAG_PATTERN.sub('', cleaned)
        
        # Handle emojis
        emoji_handling = self.normalization_config.get("handle_emojis", "keep")
        if emoji_handling == "remove":
            cleaned = self._remove_emojis(cleaned)
        elif emoji_handling == "replace":
            cleaned = self._replace_emojis(cleaned)
        
        # Normalize whitespace
        cleaned = self.WHITESPACE_PATTERN.sub(' ', cleaned)
        
        # Strip
        cleaned = cleaned.strip()
        
        # Lowercase if configured
        if self.normalization_config.get("lowercase", False):
            cleaned = cleaned.lower()
        
        return cleaned
    
    def _handle_unicode(self, tweet: Dict) -> Dict:
        """
        Handle Unicode characters in tweet data.
        
        Args:
            tweet: Tweet dictionary
            
        Returns:
            Tweet with normalized Unicode
        """
        for key, value in tweet.items():
            if isinstance(value, str):
                # Normalize Unicode (NFD -> NFC)
                tweet[key] = unicodedata.normalize('NFC', value)
        
        return tweet
    
    def _remove_emojis(self, text: str) -> str:
        """
        Remove emoji characters from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without emojis
        """
        # Emoji pattern (basic)
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)
    
    def _replace_emojis(self, text: str) -> str:
        """
        Replace emojis with descriptive text.
        
        Args:
            text: Input text
            
        Returns:
            Text with emojis replaced
        """
        # Simple replacement - could be enhanced with emoji library
        emoji_map = {
            '🚀': ' rocket ',
            '📈': ' chart_increasing ',
            '📉': ' chart_decreasing ',
            '💰': ' money ',
            '🔥': ' fire ',
            '👍': ' thumbs_up ',
            '👎': ' thumbs_down ',
            '⚠️': ' warning ',
        }
        
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
        
        return text
    
    def filter_retweets(self, tweets: List[Dict]) -> List[Dict]:
        """
        Filter out retweets.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Filtered list without retweets
        """
        if not self.cleaning_config.get("remove_retweets", True):
            return tweets
        
        filtered = []
        for tweet in tweets:
            content = tweet.get('content', '')
            # Simple heuristic: if starts with "RT @" it's a retweet
            if not content.startswith('RT @'):
                filtered.append(tweet)
        
        self.logger.info(f"Filtered retweets: {len(tweets)} -> {len(filtered)}")
        return filtered
    
    def filter_invalid_tweets(self, tweets: List[Dict]) -> List[Dict]:
        """
        Filter out invalid tweets.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Filtered list of valid tweets
        """
        valid = [t for t in tweets if t.get('is_valid', True)]
        self.logger.info(f"Filtered invalid tweets: {len(tweets)} -> {len(valid)}")
        return valid
    
    def clean_batch(self, tweets: List[Dict]) -> List[Dict]:
        """
        Clean a batch of tweets.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            List of cleaned tweets
        """
        self.logger.info(f"Cleaning {len(tweets)} tweets...")
        
        cleaned = []
        for tweet in tweets:
            try:
                cleaned_tweet = self.clean_tweet(tweet)
                cleaned.append(cleaned_tweet)
            except Exception as e:
                self.logger.error(f"Error cleaning tweet: {e}")
                continue
        
        # Apply filters
        cleaned = self.filter_retweets(cleaned)
        cleaned = self.filter_invalid_tweets(cleaned)
        
        self.logger.info(f"Cleaning complete: {len(cleaned)} tweets")
        return cleaned
