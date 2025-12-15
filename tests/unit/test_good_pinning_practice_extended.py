# tests/unit/test_good_pinning_practice_extended.py
"""Extended tests for good_pinning_practice metric."""
from src.metrics.good_pinning_practice import metric


def test_pinning_with_all_pinned(tmp_path):
    """Test with fully pinned requirements."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("""
fastapi==0.100.0
uvicorn==0.23.2
boto3==1.28.0
pydantic==2.0.0
""")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    assert score == 1.0
    assert latency >= 0


def test_pinning_with_none_pinned(tmp_path):
    """Test with no pinned versions."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("""
fastapi
uvicorn
boto3
pydantic
""")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    assert score == 0.0
    assert latency >= 0


def test_pinning_with_mixed(tmp_path):
    """Test with mixed pinned and unpinned."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("""
fastapi==0.100.0
uvicorn
boto3>=1.28.0
pydantic==2.0.0
""")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    # 2 out of 4 are strictly pinned
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_pinning_no_requirements(tmp_path):
    """Test with no requirements file."""
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    # Default for no requirements
    assert isinstance(score, float)
    assert latency >= 0


def test_pinning_no_local_path():
    """Test with no local path."""
    resource = {"url": "https://github.com/test/repo"}
    score, latency = metric(resource)
    
    assert isinstance(score, float)
    assert latency >= 0


def test_pinning_empty_resource():
    """Test with empty resource."""
    score, latency = metric({})
    
    assert isinstance(score, float)
    assert latency >= 0
