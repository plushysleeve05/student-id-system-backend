# backend/alerts_utils.py

from backend.db_config import SessionLocal
from backend.models.security_alerts_model import SecurityAlert

def push_alert_to_db(evt: dict) -> dict:
    """
    Persist an incoming event dict into the security_alerts table,
    then enrich the event dict with the new alert’s id and formatted time.

    Expects evt to have at least:
      - "type": str
      - "message" or "student": str
      - "location": str

    Returns the same evt dict, with:
      - "id": the new database PK
      - "time": formatted from the alert’s timestamp (HH:MM)
    """
    session = SessionLocal()
    try:
        # Normalize the description field for storage
        description = evt.get("message") or evt.get("student") or ""

        new_alert = SecurityAlert(
            alert_type=evt["type"],
            description=description,
            location=evt.get("location", ""),
            is_active=True,
        )
        session.add(new_alert)
        session.commit()
        session.refresh(new_alert)

        # Inject the DB id and formatted timestamp back into the event
        evt["id"]   = new_alert.id
        evt["time"] = new_alert.timestamp.strftime("%H:%M")
    finally:
        session.close()

    return evt
