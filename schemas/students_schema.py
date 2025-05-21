from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# -------- Student Schema --------
class StudentBase(BaseModel):
    student_id: str
    face_id: str
    image_name: Optional[str]  # ✅ added

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    created_at: datetime
    last_detected: Optional[datetime]
    status: Optional[str]

    class Config:
        orm_mode = True

# -------- StudentActivityLog Schema --------
class StudentActivityLogBase(BaseModel):
    student_id: str
    face_id: str
    status: str
    location: Optional[str]

class StudentActivityLogCreate(StudentActivityLogBase):
    pass

class StudentActivityLogResponse(StudentActivityLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
