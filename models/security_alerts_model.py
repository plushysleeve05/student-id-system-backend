# models/security_alerts_model.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from backend.db_config import Base

class SecurityAlert(Base):
    __tablename__ = "security_alerts"
    __table_args__ = {"extend_existing": True}   # ← allow “redefinition” on this metadata

    id          = Column(Integer, primary_key=True, index=True)
    alert_type  = Column(String,  nullable=False)    # “high” | “medium” | “low”
    description = Column(String,  nullable=False)    # human-readable message
    location    = Column(String,  nullable=False)    # e.g. camera name, “System”
    is_active   = Column(Boolean, nullable=False, server_default="true")
    timestamp   = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now()
    )
