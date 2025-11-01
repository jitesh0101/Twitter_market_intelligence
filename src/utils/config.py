"""
Configuration management utility.
Loads and validates configuration from YAML and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


class ConfigLoader:
    """Configuration loader with environment variable support."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_env()
        self._load_yaml()
        self._apply_env_overrides()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
    
    def _load_yaml(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        # Override common settings from environment
        env_overrides = {
            "LOG_LEVEL": ("logging", "level"),
            "TARGET_TWEETS": ("scraper", "target_tweets"),
            "HEADLESS_MODE": ("scraper", "browser", "headless"),
            "MAX_WORKERS": ("performance", "max_workers"),
            "MEMORY_LIMIT_MB": ("performance", "memory_limit_mb"),
        }
        
        for env_key, config_path in env_overrides.items():
            value = os.getenv(env_key)
            if value is not None:
                self._set_nested_config(config_path, value)
    
    def _set_nested_config(self, path: tuple, value: Any):
        """
        Set a nested configuration value.
        
        Args:
            path: Tuple of keys representing the path
            value: Value to set
        """
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Type conversion
        if isinstance(current.get(path[-1]), bool):
            value = value.lower() in ('true', '1', 'yes')
        elif isinstance(current.get(path[-1]), int):
            value = int(value)
        elif isinstance(current.get(path[-1]), float):
            value = float(value)
        
        current[path[-1]] = value
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            *keys: Configuration keys (e.g., 'scraper', 'target_tweets')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration dictionary."""
        return self.config
    
    def validate(self) -> bool:
        """
        Validate required configuration parameters.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        required_keys = [
            ("scraper", "hashtags"),
            ("scraper", "target_tweets"),
            ("storage", "paths", "raw_data"),
            ("storage", "paths", "processed_data"),
        ]
        
        for keys in required_keys:
            if self.get(*keys) is None:
                raise ValueError(f"Missing required configuration: {'.'.join(keys)}")
        
        # Validate hashtags
        hashtags = self.get("scraper", "hashtags")
        if not hashtags or not isinstance(hashtags, list):
            raise ValueError("Scraper hashtags must be a non-empty list")
        
        # Validate target tweets
        target = self.get("scraper", "target_tweets")
        if not isinstance(target, int) or target <= 0:
            raise ValueError("Target tweets must be a positive integer")
        
        return True


def load_config(config_path: str = "config.yaml") -> ConfigLoader:
    """
    Load and validate configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Validated ConfigLoader instance
    """
    config = ConfigLoader(config_path)
    config.validate()
    return config
