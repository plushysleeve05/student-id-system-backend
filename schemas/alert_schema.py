from pydantic import BaseModel

class AlertCreate(BaseModel):
    """
    Pydantic schema for creating a new alert.

    Fields:
      - type: severity level ("high", "medium", or "low").
      - message: human-readable description of the alert.
      - location: where the alert was triggered.
    """
    type: str
    message: str
    location: str


class AlertResponse(BaseModel):
    """
    Pydantic schema for serializing alerts over HTTP.

    Fields:
      - id: unique integer identifier for the alert.
      - type: severity level ("high", "medium", or "low").
      - message: human-readable description of the alert.
      - time: timestamp string (e.g. "11:53") when the alert occurred.
      - location: where the alert was triggered.
    """
    id: int
    type: str
    message: str
    time: str
    location: str

    class Config:
        orm_mode = True
