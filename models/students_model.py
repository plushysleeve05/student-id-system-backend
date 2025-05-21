from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from backend.db_config import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, nullable=False)
    face_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_detected = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="Active")
    image_name = Column(String, nullable=True)  # ✅ added

class StudentActivityLog(Base):
    __tablename__ = "student_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), nullable=False)
    face_id = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    location = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
