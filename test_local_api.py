"""
Local test script to mimic autograder API calls.
Tests ingestion, rating, and retrieval of models, datasets, and code.
"""
import requests
import json
import time

# Update this to your local FastAPI instance or Lambda URL
BASE_URL = "http://localhost:8000"  # Change to your API URL

def test_reset():
    """Test system reset."""
    print("\n=== Testing Reset ===")
    resp = requests.delete(f"{BASE_URL}/reset")
    print(f"Reset: {resp.status_code}")
    assert resp.status_code == 200

def test_ingest_model(name: str, url: str):
    """Test model ingestion."""
    print(f"\n=== Ingesting Model: {name} ===")
    payload = {"name": name, "url": url}
    resp = requests.post(f"{BASE_URL}/artifact/model", json=payload)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 201:
        data = resp.json()
        print(f"Model ID: {data['metadata']['id']}")
        return data['metadata']['id']
    else:
        print(f"Error: {resp.text}")
        return None

def test_rate_model(model_id: str):
    """Test rating a model."""
    print(f"\n=== Rating Model: {model_id} ===")
    resp = requests.get(f"{BASE_URL}/artifact/model/{model_id}/rate")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Net Score: {data['net_score']}")
        print(f"  Bus Factor: {data['bus_factor']}")
        print(f"  Ramp Up: {data['ramp_up_time']}")
        print(f"  Responsive: {data['responsive_maintainer']}")
        print(f"  License: {data['license']}")
        print(f"  Code Quality: {data['code_quality']}")
        print(f"  Good Pinning: {data['good_pinning_practice']}")
        print(f"  Reviewedness: {data['reviewedness']}")
        print(f"  Reproducibility: {data['reproducibility']}")
        print(f"  Treescore: {data['tree_score']}")
        print(f"  Size (AWS): {data['size_score']['aws_server']}")
        print(f"  Perf Claims: {data['performance_claims']}")
        print(f"  Dataset Quality: {data['dataset_quality']}")
        return data
    else:
        print(f"Error: {resp.text}")
        return None

def main():
    """Run all tests."""
    print("="*60)
    print("Starting Local API Tests")
    print("="*60)
    
    # Reset
    test_reset()
    
    # Test BERT model
    model_id = test_ingest_model(
        "bert-base-uncased",
        "https://huggingface.co/google-bert/bert-base-uncased"
    )
    if model_id:
        time.sleep(1)
        test_rate_model(model_id)
    
    print("\n" + "="*60)
    print("Tests Complete!")
    print("="*60)

if __name__ == "__main__":
    main()
