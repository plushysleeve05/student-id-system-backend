"""
Cache Management Utility Module

This module provides functionality for managing system cache, including:
- Clearing cached files and directories
- Getting cache statistics
- Managing cache directory structure
"""

import os
import shutil
from pathlib import Path
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.settings_model import Settings

# Set up logging for cache operations
logger = logging.getLogger(__name__)

class CacheManager:
    """
    A class to manage system cache operations.
    
    This class handles all cache-related operations including:
    - Creating and maintaining cache directory structure
    - Clearing cache files and directories
    - Providing cache statistics
    
    Attributes:
        cache_dir (Path): Path to the cache directory
    """
    
    def __init__(self, cache_dir: str = "backend/cache"):
        """
        Initialize the CacheManager with a specified cache directory.
        
        Args:
            cache_dir (str): Path to the cache directory. Defaults to "backend/cache"
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """
        Ensure the cache directory exists.
        
        Creates the cache directory and any necessary parent directories if they don't exist.
        This is called during initialization and after cache clearing operations.
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def clear_cache(self, db: Session, user_id: int) -> dict:
        """
        Clear all cached files and directories.
        
        This method:
        1. Iterates through all items in the cache directory
        2. Removes files and directories
        3. Recreates an empty cache directory
        4. Logs the operation details
        
        Returns:
            dict: A dictionary containing:
                - status: Operation status ("success")
                - message: Success message
                - cleared_items: List of cleared files and directories
        
        Raises:
            Exception: If there's an error during the cache clearing process
        """
        try:
            # Track items that are cleared for reporting
            cleared_items: List[str] = []
            
            # Iterate through all items in the cache directory
            for item in self.cache_dir.iterdir():
                if item.is_file():
                    # Remove individual files
                    item.unlink()
                    cleared_items.append(f"File: {item.name}")
                elif item.is_dir():
                    # Remove directories and their contents
                    shutil.rmtree(item)
                    cleared_items.append(f"Directory: {item.name}")

            # Recreate an empty cache directory
            self._ensure_cache_dir()

            # Log the successful operation
            logger.info(f"Cache cleared successfully. Cleared items: {cleared_items}")

            # Update user's settings with new cache stats
            user_settings = Settings.get_user_settings(db, user_id)
            if user_settings:
                user_settings.update_cache_stats(db, 0, 0)

            return {
                "status": "success",
                "message": "Cache cleared successfully",
                "cleared_items": cleared_items
            }

        except Exception as e:
            # Log and re-raise any errors that occur
            logger.error(f"Error clearing cache: {str(e)}")
            raise Exception(f"Failed to clear cache: {str(e)}")

    def get_cache_size(self) -> int:
        """
        Calculate the total size of all cached files in bytes.
        
        This method recursively traverses the cache directory and sums up
        the size of all files (excluding directories).
        
        Returns:
            int: Total size of cached files in bytes
        """
        total_size = 0
        for item in self.cache_dir.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size

    def get_cache_stats(self, db: Session, user_id: int) -> dict:
        """
        Get comprehensive statistics about the cache.
        
        This method collects information about:
        - Number of cached files
        - Number of cache directories
        - Total cache size in bytes and megabytes
        
        Returns:
            dict: A dictionary containing:
                - file_count: Number of cached files
                - directory_count: Number of cache directories
                - total_size_bytes: Total cache size in bytes
                - total_size_mb: Total cache size in megabytes (rounded to 2 decimal places)
        
        Raises:
            Exception: If there's an error while collecting cache statistics
        """
        try:
            file_count = 0
            dir_count = 0
            total_size = 0

            # Recursively traverse the cache directory
            for item in self.cache_dir.rglob("*"):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
                elif item.is_dir():
                    dir_count += 1

            stats = {
                "file_count": file_count,
                "directory_count": dir_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
            # Update user's settings with current stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            raise Exception(f"Failed to get cache statistics: {str(e)}")

# Create a global instance of the cache manager for use throughout the application
cache_manager = CacheManager()
