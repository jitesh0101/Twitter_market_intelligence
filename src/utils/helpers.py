"""
Common utility functions used across the application.
"""

import hashlib
import random
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, List, Optional

import psutil
from tenacity import retry, stop_after_attempt, wait_exponential


def generate_hash(content: str) -> str:
    """
    Generate SHA256 hash of content for deduplication.
    
    Args:
        content: Text content to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def get_random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> float:
    """
    Generate random delay for anti-detection.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
        
    Returns:
        Random delay value
    """
    return random.uniform(min_seconds, max_seconds)


def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """
    Sleep for a random human-like duration.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    time.sleep(get_random_delay(min_seconds, max_seconds))


def get_time_window(hours: int = 24) -> tuple:
    """
    Get start and end datetime for a time window.
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    return start_time, end_time


def format_number(num: int) -> str:
    """
    Format large numbers in human-readable format.
    
    Args:
        num: Number to format
        
    Returns:
        Formatted string (e.g., '1.2K', '3.4M')
    """
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)


def get_memory_usage() -> dict:
    """
    Get current memory usage statistics.
    
    Returns:
        Dictionary with memory usage information
    """
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
        "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
        "percent": process.memory_percent(),
    }


def check_memory_limit(limit_mb: int = 2048) -> bool:
    """
    Check if memory usage is within limit.
    
    Args:
        limit_mb: Memory limit in MB
        
    Returns:
        True if within limit, False otherwise
    """
    usage = get_memory_usage()
    return usage["rss_mb"] < limit_mb


def timing_decorator(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"{func.__name__} took {duration:.2f} seconds")
        return result
    
    return wrapper


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        
    Returns:
        Retry decorator
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait)
    )


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        data: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def safe_filename(filename: str) -> str:
    """
    Convert string to safe filename.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename string
    """
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    return filename


def parse_engagement_count(text: str) -> int:
    """
    Parse engagement count from text (handles K, M suffixes).
    
    Args:
        text: Text containing number (e.g., '1.2K', '3.4M')
        
    Returns:
        Integer count
    """
    text = text.strip().upper()
    
    if not text or text == '-':
        return 0
    
    try:
        if 'K' in text:
            return int(float(text.replace('K', '')) * 1000)
        elif 'M' in text:
            return int(float(text.replace('M', '')) * 1_000_000)
        else:
            return int(text.replace(',', ''))
    except (ValueError, AttributeError):
        return 0


def is_valid_tweet_content(content: str, min_length: int = 10) -> bool:
    """
    Validate tweet content.
    
    Args:
        content: Tweet content
        min_length: Minimum content length
        
    Returns:
        True if valid, False otherwise
    """
    if not content or not isinstance(content, str):
        return False
    
    content = content.strip()
    
    if len(content) < min_length:
        return False
    
    # Check if it's just whitespace or special characters
    if not any(c.isalnum() for c in content):
        return False
    
    return True


class ProgressTracker:
    """Simple progress tracking utility."""
    
    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            total: Total number of items
            description: Description of the task
        """
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, count: int = 1):
        """
        Update progress.
        
        Args:
            count: Number of items processed
        """
        self.current += count
        self._display()
    
    def _display(self):
        """Display progress information."""
        elapsed = time.time() - self.start_time
        percent = (self.current / self.total) * 100 if self.total > 0 else 0
        rate = self.current / elapsed if elapsed > 0 else 0
        
        print(
            f"\r{self.description}: {self.current}/{self.total} "
            f"({percent:.1f}%) - {rate:.1f} items/s",
            end=""
        )
    
    def finish(self):
        """Mark progress as complete."""
        self.current = self.total
        self._display()
        print()  # New line
