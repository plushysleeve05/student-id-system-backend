# routers/alerts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models.security_alerts_model import SecurityAlert
from backend.db_config import get_db
from backend.schemas.alert_schema import AlertCreate, AlertResponse

router = APIRouter(
    prefix="/security-alerts",
    tags=["security-alerts"],
)


@router.get("/", response_model=List[AlertResponse])
def list_alerts(db: Session = Depends(get_db)):
    """
    List all active alerts, most recent first.
    """
    rows = (
        db.query(SecurityAlert)
          .filter(SecurityAlert.is_active)
          .order_by(SecurityAlert.timestamp.desc())
          .all()
    )
    return [
        AlertResponse(
            id= r.id,
            type= r.alert_type,
            message= r.description,
            time= r.timestamp.strftime("%H:%M"),
            location= r.location,
        )
        for r in rows
    ]


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Fetch a single alert’s details by ID.
    """
    alert = db.query(SecurityAlert).get(alert_id)
    if not alert or not alert.is_active:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(
        id= alert.id,
        type= alert.alert_type,
        message= alert.description,
        time= alert.timestamp.strftime("%H:%M"),
        location= alert.location,
    )


@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_alert(in_alert: AlertCreate, db: Session = Depends(get_db)):
    """
    Create a new alert.
    """
    new = SecurityAlert(
        alert_type=in_alert.type,
        description=in_alert.message,
        location=in_alert.location,
        is_active = True,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return AlertResponse(
        id= new.id,
        type= new.alert_type,
        message= new.description,
        time= new.timestamp.strftime("%H:%M"),
        location= new.location,
    )


@router.delete("/{alert_id}", response_model=AlertResponse)
def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Soft-delete (“dismiss”) an alert by marking is_active=False.
    """
    alert = db.query(SecurityAlert).get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = False
    db.commit()
    return AlertResponse(
        id= alert.id,
        type= alert.alert_type,
        message= alert.description,
        time= alert.timestamp.strftime("%H:%M"),
        location= alert.location,
    )
