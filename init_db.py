from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from backend.db_config import Base, engine
import os
from backend.models import dashboard_model  # <-- This is the key
from backend.models import students_model  # <-- This is the key
from backend.models import user_model  # <-- This is the key
from backend.models import settings_model  # <-- This is the key
from backend.models import security_alerts_model  # <-- This is the key




DB_NAME = os.getenv("DB_NAME", "student_id_system")

# def create_database():
#     """Creates the PostgreSQL database if it does not exist."""
#     try:
#         temp_engine = create_engine(f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{os.getenv('DB_HOST', 'localhost')}/postgres", isolation_level="AUTOCOMMIT")
#         with temp_engine.connect() as conn:
#             result = conn.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'").fetchone()
#             if not result:
#                 conn.execute(f'CREATE DATABASE {DB_NAME}')
#                 print(f"Database '{DB_NAME}' created successfully!")
#             else:
#                 print(f"Database '{DB_NAME}' already exists.")
#     except SQLAlchemyError as e:
#         print(f"Error while creating database: {e}")

def create_tables():
    """Creates tables using SQLAlchemy ORM."""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except SQLAlchemyError as e:
        print(f"An error occurred while creating tables: {e}")

if __name__ == "__main__":
    # create_database()
    create_tables()
