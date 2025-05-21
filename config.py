import os
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "Student ID System API"
    PROJECT_VERSION: str = "1.0.0"

    POSTGRES_USER: str = os.getenv("DB_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("DB_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("DB_PORT", "5432")
    POSTGRES_DB: str = os.getenv("DB_NAME", "student_id_system")
    DATABASE_URL = os.getenv("DATABASE_URL")

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    CORS_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    print("DB_HOST =", os.getenv("DB_HOST"))
    print("SQLALCHEMY_DATABASE_URL =", DATABASE_URL)


settings = Settings()
