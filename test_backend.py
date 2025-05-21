from fastapi.testclient import TestClient
from backend.main import app  # or from backend.main import app if running from root

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the API!"}

def test_get_settings():
    response = client.get("/api/settings")
    assert response.status_code in (200, 401)  # 401 if not authenticated

def test_upload_endpoint():
    files = {"file": ("test_video.mp4", b"fakevideocontent", "video/mp4")}
    response = client.post("/upload/", files=files)
    assert response.status_code in (200, 422)  # 422 if upload validation fails
