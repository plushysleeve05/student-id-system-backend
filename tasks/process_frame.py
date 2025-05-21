# backend/tasks/process_frame.py

import cv2
import json
import numpy as np
from deepface import DeepFace

from backend.alerts_utils import push_alert_to_db
from backend.ws_broadcast import broadcast_event

from backend.tasks.match_faces import (
    detect_faces,
    COSINE_SIMILARITY_THRESHOLD,
    ML_CONFIDENCE_THRESHOLD,
    scaler,
    ml_model,
    label_encoder,
    EMBEDDING_JSON,
)

# Load known embeddings once
with open(EMBEDDING_JSON, "r") as f:
    known_embeddings = json.load(f)

async def process_frame(img: np.ndarray, mode: str):
    """
    Process one BGR frame, run either cosine‐similarity or ML pipeline,
    and return an event dict.
    """
    faces = detect_faces(img)
    if not faces:
        print("[process_frame] no face detected")
        return {"type": "warning", "message": "no face", "location": None}

    face_crop, bbox = faces[0]
    print(f"[process_frame] detected face bbox={bbox}")

    rgb = cv2.cvtColor(cv2.resize(face_crop, (160, 160)), cv2.COLOR_BGR2RGB)
    emb = DeepFace.represent(
        rgb, model_name="Facenet", enforce_detection=False
    )[0]["embedding"]
    print(f"[process_frame] computed embedding[0:5]={emb[:5]}")

    # Choose pipeline
    if mode == "ml":
        emb_s = scaler.transform([emb])
        probs = ml_model.predict(emb_s, verbose=0)[0]
        cid = int(np.argmax(probs))
        sid = label_encoder.inverse_transform([cid])[0]
        score = float(probs[cid])
        print(f"[process_frame:ML] sid={sid}, score={score:.2f}")

        student = f"Student #{sid}" if score >= ML_CONFIDENCE_THRESHOLD else "Unknown"
        evt_type = "success" if score >= ML_CONFIDENCE_THRESHOLD else "warning"
        evt = {
            "type": evt_type,
            "student": student,
            "location": "Ashesi Main Campus Entrance",
            "confidence": round(score, 2),
        }
    else:
        best_id, best_score = None, -1.0
        for sid, embs in known_embeddings.items():
            sim = np.mean([
                np.dot(emb, e) / (np.linalg.norm(emb) * np.linalg.norm(e))
                for e in embs
            ])
            if sim >= COSINE_SIMILARITY_THRESHOLD and sim > best_score:
                best_id, best_score = sid, sim
        print(f"[process_frame:Cosine] best_id={best_id}, best_score={best_score:.2f}")

        student = f"Student #{best_id}" if best_id else "Unknown"
        evt_type = "success" if best_id else "warning"
        evt = {
            "type": evt_type,
            "student": student,
            "location": "Ashesi Main Campus Entrance",
            "score": round(best_score, 2) if best_id else None,
        }

    # Persist & broadcast
    evt = push_alert_to_db(evt)
    print(f"[process_frame] broadcasting event id={evt.get('id')}: {evt}")
    await broadcast_event(evt)
    return evt
