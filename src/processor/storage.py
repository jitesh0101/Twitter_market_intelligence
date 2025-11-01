"""
Storage module for handling tweet data persistence.
Supports efficient Parquet format with compression.
"""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ..utils import Logger


class ParquetStorage:
    """Handle tweet storage in Parquet format."""
    
    def __init__(self, config: dict, logger: Logger = None):
        """
        Initialize Parquet storage handler.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or Logger.get_logger("ParquetStorage")
        
        # Extract storage configuration
        self.storage_config = config.get("storage", {})
        self.parquet_config = self.storage_config.get("parquet", {})
        self.paths_config = self.storage_config.get("paths", {})
        
        # Compression settings
        self.compression = self.parquet_config.get("compression", "snappy")
        self.engine = self.parquet_config.get("engine", "pyarrow")
        
        # Create directories
        self._ensure_directories()
        
        self.logger.info(f"ParquetStorage initialized with compression: {self.compression}")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        for path_key, path_value in self.paths_config.items():
            path = Path(path_value)
            path.parent.mkdir(parents=True, exist_ok=True)
    
    def save_raw_tweets(self, tweets: List[Dict], append: bool = False) -> str:
        """
        Save raw tweets to Parquet file.
        
        Args:
            tweets: List of tweet dictionaries
            append: Whether to append to existing file
            
        Returns:
            Path to saved file
        """
        output_path = self.paths_config.get("raw_data", "data/raw/tweets_raw.parquet")
        return self._save_to_parquet(tweets, output_path, append=append)
    
    def save_processed_tweets(self, tweets: List[Dict], append: bool = False) -> str:
        """
        Save processed tweets to Parquet file.
        
        Args:
            tweets: List of tweet dictionaries
            append: Whether to append to existing file
            
        Returns:
            Path to saved file
        """
        output_path = self.paths_config.get("processed_data", "data/processed/tweets_processed.parquet")
        return self._save_to_parquet(tweets, output_path, append=append)
    
    def save_analysis_results(self, data: pd.DataFrame, filename: str = None) -> str:
        """
        Save analysis results to Parquet file.
        
        Args:
            data: DataFrame with analysis results
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if filename:
            output_path = Path(self.paths_config.get("analysis_output", "data/analysis/")).parent / filename
        else:
            output_path = self.paths_config.get("analysis_output", "data/analysis/signals.parquet")
        
        return self._save_dataframe_to_parquet(data, output_path)
    
    def _save_to_parquet(
        self,
        tweets: List[Dict],
        output_path: str,
        append: bool = False
    ) -> str:
        """
        Save tweets to Parquet file.
        
        Args:
            tweets: List of tweet dictionaries
            output_path: Output file path
            append: Whether to append to existing file
            
        Returns:
            Path to saved file
        """
        if not tweets:
            self.logger.warning("No tweets to save")
            return output_path
        
        self.logger.info(f"Saving {len(tweets)} tweets to {output_path}")
        
        # Convert to DataFrame
        df = pd.DataFrame(tweets)
        
        # Save
        return self._save_dataframe_to_parquet(df, output_path, append=append)
    
    def _save_dataframe_to_parquet(
        self,
        df: pd.DataFrame,
        output_path: str,
        append: bool = False
    ) -> str:
        """
        Save DataFrame to Parquet file.
        
        Args:
            df: DataFrame to save
            output_path: Output file path
            append: Whether to append to existing file
            
        Returns:
            Path to saved file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if append and path.exists():
            # Load existing data and append
            existing_df = pd.read_parquet(path)
            df = pd.concat([existing_df, df], ignore_index=True)
            self.logger.info(f"Appending to existing file. Total rows: {len(df)}")
        
        # Save with compression
        df.to_parquet(
            path,
            engine=self.engine,
            compression=self.compression,
            index=False
        )
        
        file_size = path.stat().st_size / (1024 * 1024)  # MB
        self.logger.info(f"Saved {len(df)} rows to {path} ({file_size:.2f} MB)")
        
        return str(path)
    
    def load_raw_tweets(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Load raw tweets from Parquet file.
        
        Args:
            columns: Optional list of columns to load
            
        Returns:
            DataFrame with tweet data
        """
        input_path = self.paths_config.get("raw_data", "data/raw/tweets_raw.parquet")
        return self._load_from_parquet(input_path, columns=columns)
    
    def load_processed_tweets(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Load processed tweets from Parquet file.
        
        Args:
            columns: Optional list of columns to load
            
        Returns:
            DataFrame with tweet data
        """
        input_path = self.paths_config.get("processed_data", "data/processed/tweets_processed.parquet")
        return self._load_from_parquet(input_path, columns=columns)
    
    def _load_from_parquet(
        self,
        input_path: str,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Load data from Parquet file.
        
        Args:
            input_path: Input file path
            columns: Optional list of columns to load
            
        Returns:
            DataFrame with data
        """
        path = Path(input_path)
        
        if not path.exists():
            self.logger.warning(f"File not found: {path}")
            return pd.DataFrame()
        
        self.logger.info(f"Loading data from {path}")
        
        df = pd.read_parquet(
            path,
            engine=self.engine,
            columns=columns
        )
        
        self.logger.info(f"Loaded {len(df)} rows")
        return df
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        Get information about a Parquet file.
        
        Args:
            file_path: Path to Parquet file
            
        Returns:
            Dictionary with file information
        """
        path = Path(file_path)
        
        if not path.exists():
            return {"exists": False}
        
        # Get file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        
        # Get row count and schema
        parquet_file = pq.ParquetFile(path)
        num_rows = parquet_file.metadata.num_rows
        schema = parquet_file.schema_arrow
        
        return {
            "exists": True,
            "path": str(path),
            "size_mb": round(file_size_mb, 2),
            "num_rows": num_rows,
            "num_columns": len(schema),
            "columns": schema.names,
            "compression": parquet_file.metadata.row_group(0).column(0).compression
        }
    
    def load_in_chunks(
        self,
        input_path: str,
        chunk_size: int = 1000,
        columns: Optional[List[str]] = None
    ):
        """
        Generator to load Parquet file in chunks for memory efficiency.
        
        Args:
            input_path: Input file path
            chunk_size: Number of rows per chunk
            columns: Optional list of columns to load
            
        Yields:
            DataFrame chunks
        """
        path = Path(input_path)
        
        if not path.exists():
            self.logger.warning(f"File not found: {path}")
            return
        
        parquet_file = pq.ParquetFile(path)
        
        for batch in parquet_file.iter_batches(batch_size=chunk_size, columns=columns):
            df_chunk = batch.to_pandas()
            yield df_chunk
