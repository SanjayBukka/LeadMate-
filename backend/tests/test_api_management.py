import pytest
from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

# Mock get_current_user for testing
from routers.auth import get_current_user
def mock_get_current_user():
    return {"username": "testuser", "id": "test-id"}

app.dependency_overrides[get_current_user] = mock_get_current_user

def test_health_check():
    response = client.get("/api/workflow/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_analyze_repo_background():
    # This will trigger a background task
    response = client.post(
        "/api/workflow/analyze-repo",
        json={"repo_url": "https://github.com/fastapi/fastapi", "repo_name": "fastapi-test"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["message"] == "Analysis started in background"

def test_get_status_not_found():
    response = client.get("/api/workflow/status/non-existent-repo")
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"
