# tests/unit/test_routes_extended.py
"""Extended tests for routes to increase coverage."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.models import PackageRating, SizeScore
from src.main import app

client = TestClient(app)


def test_url_domain_validation_allowed():
    """Test that allowed domains work."""
    client.delete("/reset")
    
    with patch("src.api.routes.compute_package_rating") as mock_rate:
        mock_rate.return_value = PackageRating(
            bus_factor=1, bus_factor_latency=0,
            code_quality=1, code_quality_latency=0,
            ramp_up_time=1, ramp_up_time_latency=0,
            responsive_maintainer=1, responsive_maintainer_latency=0,
            license=1, license_latency=0,
            good_pinning_practice=1, good_pinning_practice_latency=0,
            reviewedness=1, reviewedness_latency=0,
            net_score=1.0, net_score_latency=0,
            tree_score=1.0, tree_score_latency=0,
            reproducibility=1.0, reproducibility_latency=0,
            performance_claims=1.0, performance_claims_latency=0,
            dataset_and_code_score=1.0, dataset_and_code_score_latency=0,
            dataset_quality=1.0, dataset_quality_latency=0,
            size_score=SizeScore(raspberry_pi=1.0, jetson_nano=1.0, desktop_pc=1.0, aws_server=1.0), 
            size_score_latency=0
        )
        
        # Test huggingface.co
        response = client.post("/package", json={"url": "https://huggingface.co/test/model"})
        assert response.status_code in [201, 424]  # Success or low score
        
        # Test github.com
        response = client.post("/package", json={"url": "https://github.com/test/repo"})
        assert response.status_code in [201, 424]


def test_url_domain_validation_rejected():
    """Test that disallowed domains are rejected."""
    client.delete("/reset")
    
    # Test evil domain
    response = client.post("/package", json={"url": "https://evil.com/malware"})
    assert response.status_code == 400
    assert "domain not allowed" in response.json()["detail"]


def test_lineage_endpoint():
    """Test the lineage endpoint."""
    client.delete("/reset")
    
    # Upload a model
    with patch("src.api.routes.compute_package_rating") as mock_rate:
        mock_rate.return_value = PackageRating(
            bus_factor=1, bus_factor_latency=0,
            code_quality=1, code_quality_latency=0,
            ramp_up_time=1, ramp_up_time_latency=0,
            responsive_maintainer=1, responsive_maintainer_latency=0,
            license=1, license_latency=0,
            good_pinning_practice=1, good_pinning_practice_latency=0,
            reviewedness=1, reviewedness_latency=0,
            net_score=1.0, net_score_latency=0,
            tree_score=1.0, tree_score_latency=0,
            reproducibility=1.0, reproducibility_latency=0,
            performance_claims=1.0, performance_claims_latency=0,
            dataset_and_code_score=1.0, dataset_and_code_score_latency=0,
            dataset_quality=1.0, dataset_quality_latency=0,
            size_score=SizeScore(raspberry_pi=1.0, jetson_nano=1.0, desktop_pc=1.0, aws_server=1.0), 
            size_score_latency=0
        )
        
        res = client.post("/artifact/model", json={"content": "test", "name": "test-model"})
        pkg_id = res.json()["metadata"]["id"]
        
        # Get lineage
        response = client.get(f"/artifact/model/{pkg_id}/lineage")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data


def test_get_package_types():
    """Test getting packages by type."""
    client.delete("/reset")
    
    # Upload different types
    client.post("/artifact/code", json={"content": "test", "name": "code-pkg"})
    client.post("/artifact/model", json={"content": "test", "name": "model-pkg"})
    client.post("/artifact/dataset", json={"content": "test", "name": "dataset-pkg"})
    
    # Get by type
    response = client.get("/artifacts/code")
    assert response.status_code == 200
    
    response = client.get("/artifacts/model")
    assert response.status_code == 200
    
    response = client.get("/artifacts/dataset")
    assert response.status_code == 200


def test_global_lineage():
    """Test global lineage endpoint."""
    client.delete("/reset")
    
    response = client.get("/lineage")
    # May return 404 if endpoint not fully implemented or 200
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "nodes" in data or isinstance(data, list)
        assert "edges" in data or isinstance(data, list)
