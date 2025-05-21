import os
import multiprocessing
import uvicorn
from config import settings

# Get the number of CPU cores
workers = multiprocessing.cpu_count()

# Configuration for production server
config = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "8000")),
    "workers": workers,
    "reload": False  # Disable auto-reload in production
}

if __name__ == "__main__":
    print(f"Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    print(f"Workers: {workers}")
    uvicorn.run(
        "main:app",
        **config
    )
