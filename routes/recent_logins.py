# backend/routes/recent_logins.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from backend.db_config import get_db
from backend.models.security_alerts_model import SecurityAlert  # ← your alerts table

router = APIRouter()


class RecentLogin(BaseModel):
    id: int
    student: str        # corresponds to alert_type or description?
    timestamp: str      # ISO‐formatted
    location: str
    status: str         # “success” vs “warning”


@router.get("/api/recent-logins", response_model=List[RecentLogin])
def get_recent_logins(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Return the most recent security alerts (faces detected),
    up to `limit` entries, newest first.
    """
    rows = (
        db.query(SecurityAlert)
        .order_by(SecurityAlert.timestamp.desc())
        .limit(limit)
        .all()
    )

    return [
        RecentLogin(
            id=alert.id,
            student=alert.description,           # show the descriptive name
            timestamp=alert.timestamp.isoformat(),
            location=alert.location,
            status="success" if alert.alert_type == "high" else "warning",
        )
        for alert in rows
    ]
