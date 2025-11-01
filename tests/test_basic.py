"""
Basic tests for Twitter Market Intelligence System.
"""

import pytest
from src.utils import generate_hash, is_valid_tweet_content, parse_engagement_count
from src.processor import DataCleaner, Deduplicator


def test_generate_hash():
    """Test hash generation."""
    content = "Test tweet content"
    hash1 = generate_hash(content)
    hash2 = generate_hash(content)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 produces 64 character hex string


def test_is_valid_tweet_content():
    """Test tweet content validation."""
    assert is_valid_tweet_content("This is a valid tweet with good content")
    assert not is_valid_tweet_content("")
    assert not is_valid_tweet_content("short")
    assert not is_valid_tweet_content("!!!")


def test_parse_engagement_count():
    """Test engagement count parsing."""
    assert parse_engagement_count("1.2K") == 1200
    assert parse_engagement_count("3.5M") == 3500000
    assert parse_engagement_count("500") == 500
    assert parse_engagement_count("") == 0
    assert parse_engagement_count("-") == 0


def test_data_cleaner():
    """Test data cleaner initialization."""
    config = {
        "processor": {
            "cleaning": {
                "remove_duplicates": True,
                "min_content_length": 10
            },
            "normalization": {
                "remove_urls": True,
                "remove_mentions": False
            }
        }
    }
    
    cleaner = DataCleaner(config)
    assert cleaner is not None


def test_deduplicator():
    """Test deduplicator initialization."""
    config = {
        "processor": {
            "deduplication": {
                "method": "content_hash",
                "similarity_threshold": 0.95
            }
        }
    }
    
    dedup = Deduplicator(config)
    assert dedup is not None
    assert dedup.method == "content_hash"


def test_deduplication_by_content_hash():
    """Test deduplication by content hash."""
    config = {
        "processor": {
            "deduplication": {
                "method": "content_hash"
            }
        }
    }
    
    tweets = [
        {"content": "Tweet 1", "username": "user1"},
        {"content": "Tweet 2", "username": "user2"},
        {"content": "Tweet 1", "username": "user1"},  # Duplicate
    ]
    
    dedup = Deduplicator(config)
    unique = dedup.deduplicate(tweets)
    
    assert len(unique) == 2


def test_text_cleaning():
    """Test text cleaning."""
    config = {
        "processor": {
            "cleaning": {},
            "normalization": {
                "remove_urls": True,
                "remove_mentions": False,
                "remove_hashtags": False
            }
        }
    }
    
    cleaner = DataCleaner(config)
    
    text = "Check this out https://example.com #trading @user"
    cleaned = cleaner.clean_text(text)
    
    assert "https://example.com" not in cleaned
    assert "#trading" in cleaned
    assert "@user" in cleaned


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
