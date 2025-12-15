from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

def test_perf_experiment_endpoint():
    """Smoke test to verify performance experiment endpoint runs."""
    # We mock _generate_dummy_data and concurrent execution to be fast
    with patch("src.api.experiment._generate_dummy_data"):
        # We also want to intercept get_package to avoid real storage
        with patch("src.api.experiment.storage.get_package") as mock_get:
            mock_get.return_value = MagicMock(data=MagicMock(content="x"))
            
            response = client.post("/admin/perf_test", json={
                "num_models": 10,
                "num_clients": 5,
                "model_size_kb": 1
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "mean_latency" in data
            assert data["total_requests"] == 5
