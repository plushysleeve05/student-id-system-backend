from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.db_config import get_db
from backend.models.dashboard_model import DashboardStat
from backend.schemas.dashboard_schema import DashboardStatCreate
from datetime import datetime

router = APIRouter()

@router.post("/api/dashboard/update", status_code=status.HTTP_201_CREATED)
def update_dashboard_stats(stat: DashboardStatCreate, db: Session = Depends(get_db)):
    existing = db.query(DashboardStat).filter(DashboardStat.date == stat.date).first()

    if existing:
        existing.total_faces += stat.total_faces
        existing.recognized_faces += stat.recognized_faces
        existing.unrecognized_faces += stat.unrecognized_faces
        existing.login_attempts += stat.login_attempts
    else:
        new_stat = DashboardStat(**stat.dict())
        db.add(new_stat)
    
    db.commit()
    return {"message": "Dashboard updated successfully"}
