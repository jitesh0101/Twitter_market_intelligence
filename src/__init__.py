"""
Twitter Market Intelligence System

A production-grade system for collecting and analyzing Twitter data
for market intelligence and trading signals.
"""

__version__ = "1.0.0"
__author__ = "Market Intelligence Team"

from .scraper import TwitterScraper, StealthDriver, HumanBehavior
from .processor import DataCleaner, Deduplicator, ParquetStorage
from .utils import (
    Logger,
    ConfigLoader,
    load_config,
    setup_logging,
    human_delay,
    generate_hash,
)

__all__ = [
    # Version
    '__version__',
    
    # Scraper
    'TwitterScraper',
    'StealthDriver',
    'HumanBehavior',
    
    # Processor
    'DataCleaner',
    'Deduplicator',
    'ParquetStorage',
    
    # Utils
    'Logger',
    'ConfigLoader',
    'load_config',
    'setup_logging',
    'human_delay',
    'generate_hash',
]
