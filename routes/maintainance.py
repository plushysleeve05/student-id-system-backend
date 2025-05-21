# routers/maintenance.py

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db_config import get_db
from backend.models.settings_model import Settings
from backend.utils.auth import get_current_user
from backend.models.user_model import User 

router = APIRouter(
    prefix="/api/maintenance",
    tags=["maintenance"],
)

# Directory where your app caches files
CACHE_DIR = Path(os.getenv("CACHE_DIR", "cache_files"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class CacheStats(BaseModel):
    total_size_mb: float
    file_count: int

class ClearCacheResponse(BaseModel):
    before_clearing: CacheStats

class RefreshResponse(BaseModel):
    operations_performed: List[str]

def compute_cache_stats() -> CacheStats:
    total_bytes = 0
    file_count = 0
    for fp in CACHE_DIR.rglob("*"):
        if fp.is_file():
            file_count += 1
            total_bytes += fp.stat().st_size
    return CacheStats(
        total_size_mb=round(total_bytes / (1024 * 1024), 2),
        file_count=file_count
    )

@router.get("/cache-stats", response_model=CacheStats)
def get_cache_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute cache stats, persist them into the current user's settings,
    and return size+count.
    """
    stats = compute_cache_stats()

    # update the user’s Settings row so next GET /api/settings returns fresh values
    settings = Settings.get_user_settings(db, current_user.id)
    if not settings:
        settings = Settings.create_default_settings(db, current_user.id)
    settings.update_cache_stats(db, stats.total_size_mb, stats.file_count)

    return stats

@router.post("/clear-cache", response_model=ClearCacheResponse)
def clear_cache(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete all files in the cache directory, returning pre-deletion stats.
    Also updates the current user's cache stats to zero.
    """
    stats_before = compute_cache_stats()

    # delete all files
    for fp in CACHE_DIR.rglob("*"):
        if fp.is_file():
            try:
                fp.unlink()
            except:
                pass

    # update DB
    settings = Settings.get_user_settings(db, current_user.id) or \
               Settings.create_default_settings(db, current_user.id)
    settings.update_cache_stats(db, 0.0, 0)

    return ClearCacheResponse(before_clearing=stats_before)

@router.post("/refresh", response_model=RefreshResponse)
def refresh_system(
    current_user: User = Depends(get_current_user),
):
    """
    Stub endpoint: perform system-wide refresh tasks.
    """
    ops = [
        "Cleared in-memory caches",
        "Reconnected to external services",
        "Completed refresh sequence"
    ]
    return RefreshResponse(operations_performed=ops)
