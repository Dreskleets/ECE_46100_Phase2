from unittest.mock import MagicMock

from src.api.models import PackageRating
from src.services.metrics_service import classify_url, compute_package_rating, load_metrics


def test_classify_url():
    assert classify_url("https://github.com/user/repo") == "CODE"
    assert classify_url("https://huggingface.co/user/model") == "MODEL"
    assert classify_url("https://huggingface.co/datasets/user/dataset") == "DATASET"
    assert classify_url("") == "CODE"
    assert classify_url(None) == "CODE"

def test_load_metrics(mocker):
    # Mock pkgutil.iter_modules to return fake modules
    fake_module_info = [
        (None, "src.metrics.fake_metric", False),
    ]
    mocker.patch("pkgutil.iter_modules", return_value=fake_module_info)
    
    # Mock importlib.import_module
    mock_module = MagicMock()
    mock_module.metric = lambda r: (0.8, 10.0)
    
    def side_effect(name):
        if name == "src.metrics":
            return MagicMock(__path__=["."], __name__="src.metrics")
        if name == "src.metrics.fake_metric":
            return mock_module
        raise ImportError(name)
        
    mocker.patch("importlib.import_module", side_effect=side_effect)
    
    metrics = load_metrics()
    assert "fake_metric" in metrics
    assert metrics["fake_metric"]({"url": "foo"}) == (0.8, 10.0)

def test_compute_package_rating_github(mocker):
    # Mock dependencies at their source
    mocker.patch("src.utils.repo_cloner.clone_repo_to_temp", return_value="/tmp/fake_repo")
    mocker.patch("shutil.rmtree")
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.listdir", return_value=["file.txt"])
    
    # Mock load_metrics to return a controlled set
    def mock_metric(r): return (0.5, 5.0)
    mocker.patch("src.services.metrics_service.load_metrics", return_value={
        "bus_factor": mock_metric,
        "code_quality": mock_metric,
        "ramp_up_time": mock_metric,
        "responsive_maintainer": mock_metric,
        "license": mock_metric,
        "good_pinning_practice": mock_metric,
        "net_score": mock_metric,
        "reviewedness": lambda r: (0.6, 6.0),
        "reproducibility": lambda r: (0.7, 7.0),
        "performance_claims": mock_metric,
        "dataset_and_code_score": mock_metric,
        "dataset_quality": mock_metric,
        "size": mock_metric,
        "treescore": lambda r: (0.8, 8.0)
    })
    
    # Mock extra metrics (TreeScore might still be explicit if I didn't remove it? 
    # I removed reviewedness and reproducibility explicit calls. 
    # TreeScore was still explicit in metrics_service.py line 208.
    # So I should keep mocking treescore if it's called explicitly.
    # But wait, metrics_service.py imports it from src.metrics.treescore.
    mocker.patch("src.metrics.treescore.compute_treescore", return_value=MagicMock(score=0.8))
    
    rating = compute_package_rating("https://github.com/user/repo")
    
    assert isinstance(rating, PackageRating)
    assert rating.bus_factor == 0.5
    assert rating.net_score == 0.5
    assert rating.reviewedness == 0.6
    assert rating.reproducibility == 0.7
    assert rating.tree_score == 0.8

def test_compute_package_rating_huggingface(mocker):
    # Mock dependencies at their source
    mocker.patch("src.utils.github_link_finder.find_github_url_from_hf", return_value="https://github.com/user/repo")
    mocker.patch("src.utils.repo_cloner.clone_repo_to_temp", return_value="/tmp/fake_repo")
    mocker.patch("shutil.rmtree")
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.listdir", return_value=["file.txt"])
    
    # Mock load_metrics
    def mock_metric(r): return (0.5, 5.0)
    mocker.patch("src.services.metrics_service.load_metrics", return_value={
        "net_score": mock_metric,
        "reviewedness": lambda r: (0.0, 0.0), # Mock failure/default
        "reproducibility": lambda r: (0.0, 0.0)
    })
    
    # Mock extra metrics to fail (cover exception paths)
    mocker.patch("src.metrics.treescore.compute_treescore", side_effect=Exception("Fail"))

    rating = compute_package_rating("https://huggingface.co/user/model")
    
    assert isinstance(rating, PackageRating)
    assert rating.reviewedness == 0.0
    assert rating.reproducibility == 0.0

