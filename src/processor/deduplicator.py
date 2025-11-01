"""
Deduplication module for tweet data.
Implements multiple strategies for finding and removing duplicates.
"""

from collections import defaultdict
from typing import Dict, List, Set

from ..utils import Logger, generate_hash


class Deduplicator:
    """Deduplicate tweets using various strategies."""
    
    def __init__(self, config: dict, logger: Logger = None):
        """
        Initialize deduplicator.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or Logger.get_logger("Deduplicator")
        
        # Extract deduplication configuration
        self.dedup_config = config.get("processor", {}).get("deduplication", {})
        self.method = self.dedup_config.get("method", "content_hash")
        self.similarity_threshold = self.dedup_config.get("similarity_threshold", 0.95)
        
        self.logger.info(f"Deduplicator initialized with method: {self.method}")
    
    def deduplicate(self, tweets: List[Dict]) -> List[Dict]:
        """
        Deduplicate tweets based on configured method.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Deduplicated list of tweets
        """
        if not tweets:
            return []
        
        self.logger.info(f"Deduplicating {len(tweets)} tweets using method: {self.method}")
        
        if self.method == "tweet_id":
            result = self._deduplicate_by_tweet_id(tweets)
        elif self.method == "content_hash":
            result = self._deduplicate_by_content_hash(tweets)
        elif self.method == "fuzzy":
            result = self._deduplicate_fuzzy(tweets)
        else:
            self.logger.warning(f"Unknown method '{self.method}', using content_hash")
            result = self._deduplicate_by_content_hash(tweets)
        
        removed_count = len(tweets) - len(result)
        self.logger.info(f"Deduplication complete: removed {removed_count} duplicates, {len(result)} unique tweets remain")
        
        return result
    
    def _deduplicate_by_tweet_id(self, tweets: List[Dict]) -> List[Dict]:
        """
        Deduplicate by tweet ID.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Deduplicated list
        """
        seen_ids: Set[str] = set()
        unique_tweets = []
        
        for tweet in tweets:
            tweet_id = tweet.get('tweet_id')
            if tweet_id and tweet_id not in seen_ids:
                seen_ids.add(tweet_id)
                unique_tweets.append(tweet)
        
        return unique_tweets
    
    def _deduplicate_by_content_hash(self, tweets: List[Dict]) -> List[Dict]:
        """
        Deduplicate by content hash (most reliable for exact duplicates).
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Deduplicated list
        """
        seen_hashes: Set[str] = set()
        unique_tweets = []
        
        for tweet in tweets:
            content = tweet.get('content', '')
            username = tweet.get('username', '')
            
            # Create hash from content + username
            content_hash = generate_hash(f"{username}_{content}")
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_tweets.append(tweet)
        
        return unique_tweets
    
    def _deduplicate_fuzzy(self, tweets: List[Dict]) -> List[Dict]:
        """
        Deduplicate using fuzzy matching for near-duplicates.
        Uses Jaccard similarity on word sets.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Deduplicated list
        """
        unique_tweets = []
        tweet_word_sets = []
        
        for tweet in tweets:
            content = tweet.get('content', '').lower()
            words = set(content.split())
            
            # Check similarity with existing tweets
            is_duplicate = False
            for existing_words in tweet_word_sets:
                similarity = self._jaccard_similarity(words, existing_words)
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tweets.append(tweet)
                tweet_word_sets.append(words)
        
        return unique_tweets
    
    @staticmethod
    def _jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
        """
        Calculate Jaccard similarity between two sets.
        
        Args:
            set1: First set
            set2: Second set
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def find_duplicates(self, tweets: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Find and group duplicate tweets.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Dictionary mapping hash to list of duplicate tweets
        """
        hash_to_tweets = defaultdict(list)
        
        for tweet in tweets:
            content = tweet.get('content', '')
            username = tweet.get('username', '')
            content_hash = generate_hash(f"{username}_{content}")
            hash_to_tweets[content_hash].append(tweet)
        
        # Filter to only duplicates
        duplicates = {k: v for k, v in hash_to_tweets.items() if len(v) > 1}
        
        total_duplicates = sum(len(v) - 1 for v in duplicates.values())
        self.logger.info(f"Found {len(duplicates)} groups of duplicates, {total_duplicates} total duplicate tweets")
        
        return duplicates
