from sqlalchemy import Boolean, Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.db_config import Base

class Settings(Base):
    """
    Settings Model
    
    Represents user settings including security preferences and cache statistics.
    Cache statistics (size and file count) are stored but updated dynamically
    through the cache manager.
    """
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Security settings
    two_factor_auth = Column(Boolean, default=False)
    session_timeout = Column(Integer, default=30)
    
    # Notification preferences
    system_notifications = Column(Boolean, default=True)
    email_alerts = Column(Boolean, default=True)
    
    # Cache statistics
    cache_size_mb = Column(Float, default=0)
    cache_file_count = Column(Integer, default=0)

    # Relationship with User model
    user = relationship("User", back_populates="settings")

    @classmethod
    def get_user_settings(cls, db, user_id: int):
        """Get settings for a specific user"""
        return db.query(cls).filter(cls.user_id == user_id).first()

    @classmethod
    def create_default_settings(cls, db, user_id: int):
        """Create default settings for a new user"""
        settings = cls(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

    def update_cache_stats(self, db, size_mb: float, file_count: int):
        """Update cache statistics"""
        self.cache_size_mb = size_mb
        self.cache_file_count = file_count
        db.commit()
        db.refresh(self)
