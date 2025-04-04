# backend/models/dashboard_model.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from backend.db_config import Base

class DashboardStats(Base):
    __tablename__ = "dashboard_stats"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(TIMESTAMP, nullable=False)

    total_faces_detected = Column(Integer, default=0)
    recognized_faces = Column(Integer, default=0)
    unrecognized_faces = Column(Integer, default=0)
    total_login_attempts = Column(Integer, default=0)

    location = Column(String(100), nullable=True)
    day_of_week = Column(String(10), nullable=True)
    updated_at = Column(TIMESTAMP, nullable=False)


class FaceActivityLog(Base):
    __tablename__ = "face_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    person_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    location = Column(String(100), nullable=True)
    timestamp = Column(TIMESTAMP, nullable=False)


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    location = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    timestamp = Column(TIMESTAMP, nullable=False)
