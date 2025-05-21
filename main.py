from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from backend.db_config import engine, Base, get_db
from backend.models.user_model import User
from backend.schemas.user_schema import UserCreate, UserResponse, UserUpdate, Token, UserRegister
from backend.schemas.settings_schema import SettingsResponse, SettingsUpdate
from backend.utils.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_superuser,
)
from backend.config import settings
from backend.routes import (
    dashboard_api,
    students_route,
    upload_route,
    alerts,
    settings_router,
    maintainance,
)
from backend.ws_broadcast import websocket_endpoint
from backend.routes.ws_live import router as ws_live_router
from backend.routes.recent_logins import router as recent_logins_router


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(students_route.router)
app.include_router(dashboard_api.router)
app.include_router(upload_route.router)
app.include_router(alerts.router)
app.include_router(maintainance.router)
app.include_router(settings_router.router)
app.include_router(ws_live_router)
app.include_router(recent_logins_router)


# WebSocket endpoint
app.add_api_websocket_route("/ws", websocket_endpoint)

# === Authentication & User Management ===
@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "is_superuser": user.is_superuser},
        expires_delta=expires,
    )
    user.update_last_login(db)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/register-superadmin", response_model=UserResponse)
async def register_superadmin(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.is_superuser == True).first():
        raise HTTPException(status_code=403, detail="Superadmin already exists.")
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=User.get_password_hash(user.password),
        is_superuser=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/users/register", response_model=UserResponse)
async def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    if User.get_by_username(db, user.username) or User.get_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Username or email already registered")
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=User.get_password_hash(user.password),
        is_superuser=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    return current_user

@app.get("/users/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    return db.query(User).offset(skip).limit(limit).all()

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in update.dict(exclude_unset=True).items():
        if field == "password":
            user.hashed_password = User.get_password_hash(value)
        else:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()

# === Settings ===
@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    current_user.ensure_settings_exist(db)
    return current_user.settings

@app.put("/api/settings", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    current_user.ensure_settings_exist(db)
    for field, value in settings_update.dict(exclude_unset=True).items():
        setattr(current_user.settings, field, value)
    db.commit()
    db.refresh(current_user.settings)
    return current_user.settings

# === Maintenance ===
@app.post("/api/maintenance/clear-cache")
async def clear_cache(
    current_user: User = Depends(get_current_active_user)
):
    before = cache_manager.get_cache_stats()
    result = cache_manager.clear_cache()
    result["before"] = before
    return result

@app.post("/api/maintenance/refresh")
async def refresh(
    current_user: User = Depends(get_current_active_user)
):
    cache_manager.clear_cache()
    return {"status": "success", "message": "System refreshed."}

@app.get("/api/maintenance/cache-stats")
async def cache_stats(
    current_user: User = Depends(get_current_active_user)
):
    return cache_manager.get_cache_stats()

# === Logout ===
@app.post("/api/logout")
async def logout():
    return {"message": "Logged out successfully"}

# === Root ===
@app.get("/")
def root():
    return {"message": "Welcome to the API!"}

if __name__ == "__main__":
    import uvicorn
    print(f"Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
