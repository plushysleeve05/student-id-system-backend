from pydantic import BaseModel, Field

class SettingsBase(BaseModel):
    two_factor_auth: bool = False
    session_timeout: int = 30
    system_notifications: bool = True
    email_alerts: bool = True
    cache_size_mb: float = Field(default=0, description="Total cache size in megabytes")
    cache_file_count: int = Field(default=0, description="Number of files in cache")

class SettingsCreate(SettingsBase):
    pass

class SettingsUpdate(BaseModel):
    two_factor_auth: bool | None = None
    session_timeout: int | None = None
    system_notifications: bool | None = None
    email_alerts: bool | None = None
    cache_size_mb: float | None = None
    cache_file_count: int | None = None

class SettingsResponse(SettingsBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
