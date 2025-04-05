# backend/schemas/dashboard_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

# -------- DashboardStats Schema --------
class DashboardStatsBase(BaseModel):
    total_faces: int
    recognized_faces: int
    unrecognized_faces: int
    login_attempts: int

class DashboardStatCreate(DashboardStatsBase):
    date: date  # Sent from the school server

class DashboardStatsResponse(DashboardStatsBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

# -------- FaceActivityLog Schema --------
class FaceActivityLogBase(BaseModel):
    student_id: Optional[str]  # can be None for unrecognized faces
    location: str
    status: str  # recognized, unrecognized, etc.

class FaceActivityLogCreate(FaceActivityLogBase):
    pass

class FaceActivityLogResponse(FaceActivityLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

# -------- SecurityAlert Schema --------
class SecurityAlertBase(BaseModel):
    title: str
    description: str
    severity: str  # e.g., 'low', 'medium', 'high'

class SecurityAlertCreate(SecurityAlertBase):
    pass

class SecurityAlertResponse(SecurityAlertBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
