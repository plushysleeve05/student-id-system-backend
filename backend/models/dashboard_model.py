# backend/models/dashboard_model.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date
from backend.db_config import Base

class DashboardStat(Base):
    __tablename__ = "dashboard_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)  # ✅ Add this line
    timestamp = Column(DateTime, default=datetime.utcnow)

    total_faces_detected = Column(Integer, default=0)
    recognized_faces = Column(Integer, default=0)
    unrecognized_faces = Column(Integer, default=0)
    total_login_attempts = Column(Integer, default=0)


class FaceActivityLog(Base):
    __tablename__ = "face_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    person_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    location = Column(String(100), nullable=True)
    timestamp = Column(DateTime, nullable=False)


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    location = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    timestamp = Column(DateTime, nullable=False)
