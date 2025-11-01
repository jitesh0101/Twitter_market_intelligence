"""
Logging utility with colored console output and file logging.
Provides structured logging for the entire application.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

import colorlog


class Logger:
    """Custom logger with color support and file rotation."""
    
    _loggers = {}
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        log_file: Optional[str] = None,
        level: str = "INFO",
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
        console_output: bool = True
    ) -> logging.Logger:
        """
        Get or create a logger with the specified configuration.
        
        Args:
            name: Logger name
            log_file: Path to log file (optional)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            console_output: Whether to output to console
            
        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        logger.handlers = []  # Clear existing handlers
        
        # Console handler with colors
        if console_output:
            console_handler = colorlog.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            
            console_format = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            
            file_format = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger


def setup_logging(config: dict) -> logging.Logger:
    """
    Setup logging based on configuration.
    
    Args:
        config: Configuration dictionary with logging settings
        
    Returns:
        Main application logger
    """
    log_config = config.get("logging", {})
    
    logger = Logger.get_logger(
        name="twitter_intelligence",
        log_file=log_config.get("file", "logs/app.log"),
        level=log_config.get("level", "INFO"),
        max_bytes=log_config.get("max_bytes", 10485760),
        backup_count=log_config.get("backup_count", 5),
        console_output=log_config.get("console_output", True)
    )
    
    logger.info("Logging system initialized")
    return logger
