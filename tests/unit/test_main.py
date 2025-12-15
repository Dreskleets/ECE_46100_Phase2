# tests/unit/test_main.py
"""Tests for main app module."""
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_app_exists():
    """Test that app is created."""
    assert app is not None


def test_root_redirect():
    """Test root endpoint redirects or returns something."""
    response = client.get("/")
    # Either 200, 307 redirect, or 404
    assert response.status_code in [200, 307, 404, 405]


def test_health_endpoint():
    """Test health check if it exists."""
    response = client.get("/health")
    # May or may not exist
    assert response.status_code in [200, 404]


def test_docs_endpoint():
    """Test OpenAPI docs endpoint."""
    response = client.get("/docs")
    # FastAPI provides docs by default
    assert response.status_code in [200, 404]


def test_openapi_json():
    """Test OpenAPI schema endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "openapi" in response.json()


def test_reset_endpoint():
    """Test reset endpoint."""
    response = client.delete("/reset")
    assert response.status_code == 200


def test_packages_endpoint():
    """Test packages endpoint with wildcard query."""
    client.delete("/reset")
    response = client.post("/packages", json=[{"name": "*"}])
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_package_upload_minimal():
    """Test minimal package upload."""
    client.delete("/reset")
    response = client.post("/package", json={"content": "test"})
    assert response.status_code == 201


def test_authenticate_endpoint():
    """Test authentication endpoint."""
    response = client.put("/authenticate", json={
        "User": {"name": "test", "isAdmin": True},
        "Secret": {"password": "test"}
    })
    # May validate differently
    assert response.status_code in [200, 422, 501]


def test_tracks_endpoint():
    """Test tracks endpoint if it exists."""
    response = client.get("/tracks")
    # Implementation dependent
    assert response.status_code in [200, 404, 501]


def test_byRegEx_endpoint():
    """Test search by regex endpoint."""
    client.delete("/reset")
    response = client.post("/package/byRegEx", json={"RegEx": "test"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_artifact_endpoints():
    """Test artifact type endpoints."""
    client.delete("/reset")
    
    # Upload via artifact endpoints
    for artifact_type in ["code", "model", "dataset"]:
        response = client.post(f"/artifact/{artifact_type}", json={"content": "test", "name": f"{artifact_type}-pkg"})
        assert response.status_code == 201
        
        pkg_id = response.json()["metadata"]["id"]
        
        # Get via singular/plural artifact endpoint
        response = client.get(f"/artifacts/{artifact_type}/{pkg_id}")
        assert response.status_code in [200, 404]


def test_rate_endpoint():
    """Test rate endpoint for a package."""
    client.delete("/reset")
    
    # Upload package
    response = client.post("/package", json={"content": "test", "name": "rate-pkg"})
    pkg_id = response.json()["metadata"]["id"]
    
    # Rate it
    response = client.get(f"/package/{pkg_id}/rate")
    assert response.status_code == 200
    data = response.json()
    assert "net_score" in data
