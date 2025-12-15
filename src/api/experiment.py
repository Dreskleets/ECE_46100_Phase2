"""
Experiment API Module.

Provides endpoints for running performance experiments and benchmarks on the registry.
"""
import concurrent.futures
import logging
import random
import statistics
import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.models import Package, PackageData, PackageMetadata
from src.services.storage import storage

router = APIRouter(prefix="/admin", tags=["experiment"])

logger = logging.getLogger("phase1_api")

class PerfTestRequest(BaseModel):
    num_models: int = Field(500, description="Number of models in registry")
    num_clients: int = Field(100, description="Number of concurrent clients")
    model_size_kb: int = Field(1, description="Size of dummy model in KB")

class PerfTestResult(BaseModel):
    mean_latency: float
    median_latency: float
    p99_latency: float
    throughput_req_per_sec: float
    total_time: float
    total_requests: int
    errors: int

def _generate_dummy_data(count: int, size_kb: int):
    """Ensure registry has enough dummy packages."""
    logger.info(f"Checking/Generating {count} dummy packages...")
    
    # Check if packages exist (simple check: check last one)
    last_id = f"perf-{count-1}"
    if storage.get_package(last_id):
        logger.info("Dummy data appears to exist. Skipping generation.")
        return

    # Generate content
    content = "x" * (size_kb * 1024)
    import base64
    b64_content = base64.b64encode(content.encode()).decode()

    for i in range(count):
        pkg = Package(
            metadata=PackageMetadata(
                name=f"PerfPackage-{i}",
                version="1.0.0",
                id=f"perf-{i}",
                type="model"
            ),
            data=PackageData(
                content=b64_content,
                readme="# Perf Test"
            )
        )
        storage.add_package(pkg)
    logger.info("Dummy data generation complete.")

def _run_client_task(client_id: int, num_models: int):
    """Simulate a single client downloading a random model."""
    target_id = f"perf-{random.randint(0, num_models-1)}"
    start = time.time()
    try:
        pkg = storage.get_package(target_id)
        if not pkg:
            raise Exception("Package not found")
        # Simulate 'download' by accessing content
        _ = pkg.data.content
        duration = time.time() - start
        return duration, True
    except Exception as e:
        logger.error(f"Client {client_id} error: {e}")
        return time.time() - start, False

@router.post("/perf_test", response_model=PerfTestResult)
def run_performance_test(req: PerfTestRequest):
    """
    Run a performance test simulating clients downloading models.
    
    Experiment Design:
    1. Populates registry with `num_models` dummy packages (if missing).
    2. Spawns `num_clients` concurrent threads.
    3. Each client requests a random package from the registry.
    4. Measures time to retrieve the package.
    
    This allows benchmarking different backends (S3 vs SQLite vs FS) and 
    optimizations (Caching) by changing env vars 'STORAGE_TYPE' and 'ENABLE_CACHE'.
    """
    
    # 1. Setup Data
    _generate_dummy_data(req.num_models, req.model_size_kb)
    
    # 2. Run Clients
    latencies = []
    errors = 0
    start_time = time.time()
    
    # Use ThreadPoolExecutor to simulate concurrency
    # Note: For CPU-bound tasks, threads are limited by GIL, 
    # but I/O bound tasks (like Storage/DB access) release GIL.
    # storage.get_package for LocalStorage is mostly I/O (file read) or SQLite (db read).
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=req.num_clients) as executor:
        futures = [
            executor.submit(_run_client_task, i, req.num_models) 
            for i in range(req.num_clients)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            lat, success = future.result()
            latencies.append(lat)
            if not success:
                errors += 1
                
    total_time = time.time() - start_time
    
    # 3. Calculate Stats
    if not latencies:
        return PerfTestResult(
            mean_latency=0, median_latency=0, p99_latency=0,
            throughput_req_per_sec=0, total_time=total_time,
            total_requests=req.num_clients, errors=errors
        )
        
    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    try:
        p99_lat = statistics.quantiles(latencies, n=100)[98] # 99th percentile approx
    except Exception:
        # Fallback for small sample
        latencies.sort()
        p99_lat = latencies[int(len(latencies)*0.99)]
        
    throughput = req.num_clients / total_time
    
    return PerfTestResult(
        mean_latency=mean_lat,
        median_latency=median_lat,
        p99_latency=p99_lat,
        throughput_req_per_sec=throughput,
        total_time=total_time,
        total_requests=req.num_clients,
        errors=errors
    )
