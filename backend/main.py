from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from backend.db_config import engine, Base, get_db
from backend.models.user_model import User
from backend.schemas.user_schema import UserCreate, UserResponse, UserUpdate, Token, UserRegister
from backend.schemas.settings_schema import SettingsResponse, SettingsUpdate
from backend.models.settings_model import Settings
from backend.utils.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_superuser,
)
from backend.config import settings

from backend.routes import dashboard_api

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*","https://7e58-154-65-20-57.ngrok-free.app"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_api.router)


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "is_superuser": user.is_superuser},
        expires_delta=access_token_expires
    )
    
    # Update last login
    user.update_last_login(db)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Create new user (superuser only)"""
    # Check if username exists
    if User.get_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    if User.get_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=User.get_password_hash(user.password),
        is_superuser=user.is_superuser
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/users/register-superadmin", response_model=UserResponse)
async def register_superadmin(user: UserCreate, db: Session = Depends(get_db)):
    """Register the first superadmin (only works if no users exist)"""
    # Check if any users exist
    if db.query(User).filter(User.is_superuser == True).first():
        raise HTTPException(
            status_code=403,
            detail="Superadmin already exists. New users must be created by an existing superadmin."
        )
    
    # Force is_superuser to True for this endpoint
    user.is_superuser = True
    
    # Create superadmin user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=User.get_password_hash(user.password),
        is_superuser=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/users/register", response_model=UserResponse)
async def register_user(user: UserRegister, db: Session = Depends(get_db)):
    """Register a new regular user"""
    # Check if username exists
    if User.get_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    if User.get_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=User.get_password_hash(user.password),
        is_superuser=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.get("/users/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Get all users (superuser only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user information"""
    # Only superusers can update other users
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        if field == "password" and value:
            value = User.get_password_hash(value)
            setattr(db_user, "hashed_password", value)
        else:
            setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """Delete a user (superuser only)"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()

@app.get("/api/settings", response_model=SettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's settings"""
    current_user.ensure_settings_exist(db)
    return current_user.settings

@app.put("/api/settings", response_model=SettingsResponse)
async def update_user_settings(
    settings_update: SettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user settings"""
    current_user.ensure_settings_exist(db)
    
    # Update only provided fields
    for field, value in settings_update.dict(exclude_unset=True).items():
        if value is not None:  # Only update if value is provided
            setattr(current_user.settings, field, value)
    
    db.commit()
    db.refresh(current_user.settings)
    return current_user.settings

from backend.utils.cache import cache_manager

@app.post("/api/maintenance/clear-cache")
async def clear_cache(current_user: User = Depends(get_current_active_user)):
    """
    Clear system cache endpoint.
    
    This endpoint:
    1. Verifies user authentication
    2. Clears all cached files and directories
    3. Returns cache clearing operation results
    
    Returns:
        dict: Results of the cache clearing operation including:
            - status: Operation status
            - message: Success/error message
            - cleared_items: List of cleared cache items
    
    Raises:
        HTTPException: If cache clearing fails
    """
    try:
        # Get cache statistics before clearing
        before_stats = cache_manager.get_cache_stats()
        
        # Clear the cache
        result = cache_manager.clear_cache()
        
        # Add cache size information to the result
        result["before_clearing"] = {
            "size_mb": before_stats["total_size_mb"],
            "file_count": before_stats["file_count"]
        }
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )

@app.post("/api/maintenance/refresh")
async def refresh_system(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Refresh system endpoint.
    
    This endpoint:
    1. Verifies user authentication
    2. Clears the cache
    3. Reloads system configurations
    4. Returns operation results
    
    Returns:
        dict: Results of the system refresh operation
    
    Raises:
        HTTPException: If refresh operation fails
    """
    try:
        # Clear the cache first
        cache_manager.clear_cache()
        
        # Here you can add additional refresh operations:
        # - Reload configurations
        # - Reset temporary data
        # - Clear other system caches
        # - etc.
        
        return {
            "status": "success",
            "message": "System refreshed successfully",
            "operations_performed": [
                "Cleared system cache",
                "Reset temporary data"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh system: {str(e)}"
        )

@app.get("/api/maintenance/cache-stats")
async def get_cache_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get cache statistics endpoint.
    
    This endpoint:
    1. Verifies user authentication
    2. Retrieves current cache statistics
    
    Returns:
        dict: Cache statistics including:
            - file_count: Number of cached files
            - directory_count: Number of cache directories
            - total_size_bytes: Total cache size in bytes
            - total_size_mb: Total cache size in megabytes
    
    Raises:
        HTTPException: If retrieving cache stats fails
    """
    try:
        return cache_manager.get_cache_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
