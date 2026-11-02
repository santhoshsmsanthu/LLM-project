from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["message"] == "MCC Classification Service is running"


def test_clients_endpoint():
    response = client.get("/api/clients")

    assert response.status_code == 200
    assert response.json() == ["default"]
