# routers/settings.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db_config import get_db
from backend.models.settings_model import Settings
from backend.schemas.settings_schema import SettingsResponse, SettingsUpdate
from backend.utils.auth import get_current_user  # your existing auth dependency
from backend.models.user_model import User  # adjust if your User model import is different

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
)

@router.get("/", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the settings row for the current user, creating defaults if missing.
    """
    settings = Settings.get_user_settings(db, current_user.id)
    if not settings:
        settings = Settings.create_default_settings(db, current_user.id)
    return settings

@router.put("/", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update one or more user settings fields.
    """
    settings = Settings.get_user_settings(db, current_user.id)
    if not settings:
        settings = Settings.create_default_settings(db, current_user.id)

    update_data = payload.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No settings fields provided")

    # Prevent users from manually overriding cache stats here
    for key in ("cache_size_mb", "cache_file_count"):
        update_data.pop(key, None)

    for key, value in update_data.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)
    return settings
