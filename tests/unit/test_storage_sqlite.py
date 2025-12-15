import pytest
import os
from src.services.storage import SQLiteStorage, CachedStorage
from src.api.models import Package, PackageMetadata, PackageData, PackageQuery

@pytest.fixture
def sample_package():
    meta = PackageMetadata(
        name="TestPkg", version="1.0.0", id="test-1", type="code"
    )
    data = PackageData(content="base64enc", readme="# Readme")
    return Package(metadata=meta, data=data)

@pytest.fixture
def sqlite_store(tmp_path):
    db_file = tmp_path / "test_registry.db"
    store = SQLiteStorage(db_path=str(db_file))
    return store

def test_sqlite_init(sqlite_store):
    assert os.path.exists(sqlite_store.db_path)

def test_sqlite_add_get(sqlite_store, sample_package):
    sqlite_store.add_package(sample_package)
    retrieved = sqlite_store.get_package("test-1")
    assert retrieved is not None
    assert retrieved.metadata.name == "TestPkg"
    assert retrieved.data.content == "base64enc"

def test_sqlite_list(sqlite_store, sample_package):
    sqlite_store.add_package(sample_package)
    res = sqlite_store.list_packages()
    assert len(res) == 1
    assert res[0].id == "test-1"

def test_sqlite_search_regex(sqlite_store, sample_package):
    sqlite_store.add_package(sample_package)
    # Search by name regex
    res = sqlite_store.search_by_regex("Test.*")
    assert len(res) == 1
    # Search by readme regex
    res2 = sqlite_store.search_by_regex("Read.*")
    assert len(res2) == 1
    # Miss
    res3 = sqlite_store.search_by_regex("Nomatch")
    assert len(res3) == 0

def test_sqlite_delete_reset(sqlite_store, sample_package):
    sqlite_store.add_package(sample_package)
    assert sqlite_store.delete_package("test-1") is True
    assert sqlite_store.get_package("test-1") is None
    
    sqlite_store.add_package(sample_package)
    sqlite_store.reset()
    assert sqlite_store.get_package("test-1") is None

def test_cached_storage(sqlite_store, sample_package):
    cached = CachedStorage(sqlite_store)
    
    # Add via wrapper
    cached.add_package(sample_package)
    
    # Get (miss -> hit)
    p1 = cached.get_package("test-1")
    assert p1 is not None
    
    # Get (hit - manipulate DB behind back to prove cache used)
    # Delete from DB directly
    sqlite_store.delete_package("test-1")
    
    # Should still get from cache
    p2 = cached.get_package("test-1")
    assert p2 is not None
    
    # Delete via wrapper clears cache
    cached.delete_package("test-1")
    p3 = cached.get_package("test-1")
    assert p3 is None
