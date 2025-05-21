# backend/routes/upload_route.py

import os
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from backend.tasks.match_faces import detect_and_match
from backend.tasks.process_frame import process_frame

import cv2
import numpy as np

router = APIRouter()

@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form("matching")
):
    UPLOAD_DIR = os.path.abspath("video_uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    out_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(out_path, "wb") as f:
        f.write(await file.read())

    background_tasks.add_task(detect_and_match, out_path, mode)
    return {"status": "processing"}


