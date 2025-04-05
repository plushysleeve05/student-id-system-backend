from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.db_config import get_db
from backend.models.dashboard_model import DashboardStat
from backend.schemas.dashboard_schema import DashboardStatCreate
from datetime import datetime
from typing import List

router = APIRouter()

@router.post("/api/dashboard/update", status_code=status.HTTP_201_CREATED)
def update_dashboard_stats(stat: DashboardStatCreate, db: Session = Depends(get_db)):
    existing = db.query(DashboardStat).filter(DashboardStat.date == stat.date).first()

    if existing:
        existing.total_faces_detected += stat.total_faces_detected
        existing.recognized_faces += stat.recognized_faces
        existing.unrecognized_faces += stat.unrecognized_faces
        existing.total_login_attempts += stat.total_login_attempts
    else:
        new_stat = DashboardStat(**stat.dict())
        db.add(new_stat)
    
    db.commit()
    return {"message": "Dashboard updated successfully"}


@router.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    stats = db.query(
        func.sum(DashboardStat.total_faces_detected).label("total_faces"),
        func.sum(DashboardStat.recognized_faces).label("recognized_faces"),
        func.sum(DashboardStat.unrecognized_faces).label("unrecognized_faces"),
        func.sum(DashboardStat.total_login_attempts).label("login_attempts"),
    ).first()

    return {
        "totalFaces": stats.total_faces or 0,
        "recognizedFaces": stats.recognized_faces or 0,
        "unrecognizedFaces": stats.unrecognized_faces or 0,
        "loginAttempts": stats.login_attempts or 0
    }

