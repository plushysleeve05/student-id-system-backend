from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.db_config import get_db
from backend.models.students_model import Student, StudentActivityLog
from backend.schemas.students_schema import StudentCreate, StudentActivityLogCreate, StudentResponse, StudentActivityLogResponse
from datetime import datetime
from typing import List

router = APIRouter()

# Add or update a student record
@router.post("/api/students/", status_code=status.HTTP_201_CREATED)
def add_or_update_student(student: StudentCreate, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.student_id == student.student_id).first()

    if existing_student:
        # If the student already exists, just update the face ID and last detected time
        existing_student.face_id = student.face_id
        existing_student.last_detected = datetime.utcnow()
        existing_student.status = "Active"
        existing_student.image_name = student.image_name  # ✅ update if changed
    else:
        new_student = Student(**student.dict())
        db.add(new_student)

    db.commit()
    return {"message": "Student record added or updated successfully"}

# Get all students
@router.get("/api/students/", response_model=List[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).all()

# Add a student activity log (face recognition attempt)
@router.post("/api/students/activity-log/", status_code=status.HTTP_201_CREATED)
def add_activity_log(log: StudentActivityLogCreate, db: Session = Depends(get_db)):
    new_log = StudentActivityLog(**log.dict())
    db.add(new_log)
    db.commit()
    return {"message": "Student activity log added successfully"}

# Get all activity logs for a student
@router.get("/api/students/{student_id}/activity-log", response_model=List[StudentActivityLogResponse])
def get_student_activity_log(student_id: str, db: Session = Depends(get_db)):
    return db.query(StudentActivityLog).filter(StudentActivityLog.student_id == student_id).all()
