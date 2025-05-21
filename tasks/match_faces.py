# backend/tasks/match_faces.py

import os
import sys
import cv2
import json
import torch
import asyncio
import numpy as np
import joblib

from collections import Counter
from deepface import DeepFace
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import InputLayer
from tensorflow.keras.mixed_precision import Policy as DTypePolicy
import albumentations as A

from backend.ws_broadcast import broadcast_event
from backend.alerts_utils import push_alert_to_db  # ← our new helper

# ─── CONFIG ───────────────────────────────────────────────────────────────
YOLO_WEIGHTS       = "/home/ayombalima/YOLO-FaceV2-master/yolov5s_v2.pt"
EMBEDDING_JSON     = "/home/ayombalima/YOLO-FaceV2-master/augmented_student_embeddings3.json"
CLUSTER_JSON       = "/home/ayombalima/ml_models/final_clustered_results.json"
ML_MODEL_PATH      = "/home/ayombalima/ml_models/student_recognition_model.h5"
SCALER_PATH        = "/home/ayombalima/ml_models/scaler.pkl"
LABEL_ENCODER_PATH = "/home/ayombalima/ml_models/label_encoder.pkl"

EXTRACTED_DIR = "extracted_frames"
RESIZED_DIR   = "resized_frames"
DETECTED_DIR  = "detected_faces"
MATCHED_DIR   = "matched_faces"
for d in (EXTRACTED_DIR, RESIZED_DIR, DETECTED_DIR, MATCHED_DIR):
    os.makedirs(d, exist_ok=True)

DEDUP_WINDOW = 10  # seconds

# ─── THRESHOLDS ────────────────────────────────────────────────────────────
ML_CONFIDENCE_THRESHOLD      = 0.80
COSINE_SIMILARITY_THRESHOLD  = 0.75

# ─── YOLO / TORCH SETUP ───────────────────────────────────────────────────
sys.path.append("/home/ayombalima/YOLO-FaceV2-master")
from models.experimental import attempt_load
from utils.general       import non_max_suppression, scale_coords
from utils.torch_utils   import select_device

device     = select_device("cpu")
yolo_model = attempt_load(YOLO_WEIGHTS, map_location=device).eval()

class CustomInputLayer(InputLayer):
    def __init__(self, *args, **kwargs):
        bs = kwargs.pop("batch_shape", None)
        if bs is not None:
            kwargs["batch_input_shape"] = bs
        super().__init__(*args, **kwargs)

ml_model      = load_model(
    ML_MODEL_PATH,
    compile=False,
    safe_mode=False,
    custom_objects={"InputLayer": CustomInputLayer, "DTypePolicy": DTypePolicy}
)
scaler        = joblib.load(SCALER_PATH)
label_encoder = joblib.load(LABEL_ENCODER_PATH)

with open(CLUSTER_JSON) as f:
    clusters_map = json.load(f).get("clusters", {})

# ─── AUGMENTATIONS ────────────────────────────────────────────────────────
aug_pipeline = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.Rotate(limit=15, p=0.6),
    A.RandomBrightnessContrast(p=0.6),
    A.GaussNoise(p=0.2),
    A.HueSaturationValue(p=0.3),
    A.RandomShadow(p=0.2),
])

# ─── HELPERS ──────────────────────────────────────────────────────────────
def map_student_id_to_images(student_id):
    paths = []
    for _, items in clusters_map.items():
        for item in items:
            if item.get("student_id") == student_id:
                p = item.get("image_path")
                if p:
                    paths.append(p)
                    if len(paths) >= 8:
                        return paths
    return paths

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    areaA = (boxA[2]-boxA[0]) * (boxA[3]-boxA[1])
    areaB = (boxB[2]-boxB[0]) * (boxB[3]-boxB[1])
    if areaA + areaB - inter == 0:
        return 0
    return inter / (areaA + areaB - inter)

def detect_faces(img, conf_thres=0.25, iou_thres=0.45):
    tensor = (
        torch.from_numpy(img)
             .permute(2,0,1).float().div(255.0)
             .unsqueeze(0).to(device)
    )
    with torch.no_grad():
        dets = non_max_suppression(
            yolo_model(tensor)[0],
            conf_thres=conf_thres,
            iou_thres=iou_thres
        )[0]
    if dets is None or len(dets) == 0:
        return []
    dets[:, :4] = scale_coords(tensor.shape[2:], dets[:, :4], img.shape).round()
    faces = []
    for d in dets:
        x1,y1,x2,y2 = map(int, d[:4])
        crop = img[y1:y2, x1:x2]
        if crop.size:
            faces.append((crop, (x1,y1,x2,y2)))
    return faces

def extract_and_resize(video_path, interval=60):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    fid, saved = 0, 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if fid % interval == 0:
            name = f"frame{fid}.jpg"
            rot  = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            cv2.imwrite(os.path.join(EXTRACTED_DIR, name), rot)
            small = cv2.resize(rot, (640,640))
            cv2.imwrite(os.path.join(RESIZED_DIR,   name), small)
            saved += 1
        fid += 1
    cap.release()
    print(f"[extract] Extracted {saved} frames.")

# ─── COSINE PIPELINE ──────────────────────────────────────────────────────
async def full_cosine_pipeline(video_path):
    print("[cosine] Starting cosine-matching…")
    extract_and_resize(video_path)
    with open(EMBEDDING_JSON) as f:
        known = json.load(f)

    tracks = []
    for fn in sorted(os.listdir(RESIZED_DIR)):
        img = cv2.imread(os.path.join(RESIZED_DIR, fn))
        faces = detect_faces(img)
        for crop, bbox in faces:
            if not any(iou(tr['bbox'], bbox) > 0.5 for tr in tracks):
                tracks.append({'bbox': bbox, 'crop': crop})

    for tr in tracks:
        emb = DeepFace.represent(
            cv2.cvtColor(cv2.resize(tr['crop'], (160,160)), cv2.COLOR_BGR2RGB),
            model_name="Facenet", enforce_detection=False
        )[0]['embedding']

        best_id, best_score = None, -1
        for sid, embs in known.items():
            score = np.mean([np.dot(emb,e)/(np.linalg.norm(emb)*np.linalg.norm(e)) for e in embs])
            if score >= COSINE_SIMILARITY_THRESHOLD and score > best_score:
                best_id, best_score = sid, score

        evt = {
            "type": "success" if best_id else "warning",
            "student": f"Student #{best_id}" if best_id else "Unknown",
            "location": "Ashesi Main Campus Entrance",
            "score": round(float(best_score), 2) if best_score > 0 else None
        }

        evt = push_alert_to_db(evt)
        print(f"[cosine] Broadcasting (DB id={evt['id']}): {evt}")
        await broadcast_event(evt)

    print("[cosine] Completed.")

# ─── MLP PIPELINE ─────────────────────────────────────────────────────────
def run_ml_pipeline(video_path):
    print("[ml] Starting ML classification…")
    extract_and_resize(video_path)

    tracks = []
    for fn in sorted(os.listdir(RESIZED_DIR)):
        img = cv2.imread(os.path.join(RESIZED_DIR, fn))
        faces = detect_faces(img)
        for crop, bbox in faces:
            # fixed: wrap generator in list for np.mean
            if not any(np.mean([min(b1,b2) for b1,b2 in zip(tr['bbox'], bbox)]) > 0.5 for tr in tracks):
                tracks.append({'bbox': bbox, 'crop': crop})

    if not tracks:
        print("[ml] No faces found—skipping.")
        return

    for tr in tracks:
        votes = []
        for _ in range(5):
            aug = aug_pipeline(image=tr['crop'])["image"]
            face160 = cv2.resize(aug, (160,160))
            emb = DeepFace.represent(
                cv2.cvtColor(face160, cv2.COLOR_BGR2RGB),
                model_name="Facenet", enforce_detection=False
            )[0]["embedding"]

            emb_s = scaler.transform([emb])
            probs = ml_model.predict(emb_s, verbose=0)[0]
            cid = int(np.argmax(probs))
            sid = label_encoder.inverse_transform([cid])[0]
            votes.append((sid, probs[cid]))

        final_sid = Counter([v[0] for v in votes]).most_common(1)[0][0]
        avg_confidence = np.mean([conf for sid, conf in votes if sid == final_sid])

        evt = {
            "type": "success" if avg_confidence >= ML_CONFIDENCE_THRESHOLD else "warning",
            "student": f"Student #{final_sid}" if avg_confidence >= ML_CONFIDENCE_THRESHOLD else "Unknown",
            "location": "Ashesi Main Campus Entrance",
            "confidence": float(avg_confidence)
        }

        evt = push_alert_to_db(evt)
        print(f"[ml] Broadcasting (DB id={evt['id']}): {evt}")
        asyncio.run(broadcast_event(evt))

# ─── DISPATCH ────────────────────────────────────────────────────────────
async def detect_and_match(video_path, mode="matching"):
    # Clean up old frames
    for d in (EXTRACTED_DIR, RESIZED_DIR, DETECTED_DIR, MATCHED_DIR):
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))

    print(f"[dispatch] mode={mode}")
    if mode == "ml":
        await asyncio.to_thread(run_ml_pipeline, video_path)
    else:
        await full_cosine_pipeline(video_path)
