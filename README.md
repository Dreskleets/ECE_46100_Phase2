# Trustworthy Model Registry (Phase 2)

## Purpose
The **Trustworthy Model Registry** is a secure, scalable system designed to ingest, assess, and manage open-source software packages and machine learning models. It provides automated quality scoring based on metrics such as Bus Factor, Responsiveness, and Correctness, ensuring that only high-quality artifacts are reused.

Key Features:
- **Automated Metric Calculation**: Scores packages on maintainability and security.
- **RESTful API**: Comprehensive API for package management (OpenAPI compliant).
- **Performance Optimized**: Swappable backends (SQLite/S3) and caching layers.
- **Secure**: Implements role-based access control and input validation.

## Configuration
Configure the system using environment variables or a `.env` file in the root directory.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `STORAGE_TYPE` | Backend storage engine (`LOCAL`, `SQLITE`, `S3`) | `LOCAL` |
| `ENABLE_CACHE` | Enable in-memory LRU caching (`true`/`false`) | `false` |
| `BUCKET_NAME` | S3 Bucket name (if S3 storage used) | `ece46100-registry` |
| `AWS_REGION` | AWS Region (if S3 used) | `us-east-1` |
| `LOG_LEVEL` | Logging verbosity (0=WARNING, 1=INFO, 2=DEBUG) | `0` |
| `GITHUB_TOKEN` | GitHub API Token for metrics calculation | **Required** |

## Deployment
The application is designed to be deployed as a serverless function (AWS Lambda) or a containerized service.

### AWS Lambda Deployment
1.  **Build**: Package the application using `zip`.
    ```bash
    zip -r package.zip src/ vendor/ run.py requirements.txt
    ```
2.  **Deploy**: Upload to AWS Lambda.
    ```bash
    aws lambda update-function-code --function-name MyRegistry --zip-file fileb://package.zip
    ```
3.  **Configure**: Set environment variables in the Lambda configuration console.

### Local Development
1.  **Install**: `pip install -r requirements.txt`
2.  **Run**: `./run.py` or `uvicorn src.main:app --reload`
3.  **Test**: `./run test` or `pytest`

## Interaction
Interact with the registry via the CLI or HTTP API.

### CLI Usage
*   **Install Dependencies**: `./run install`
*   **Run Tests**: `./run test`
*   **Process URL File**: `./run path/to/urls.txt` (Calculates scores for list of packages)

### API Usage
Detailed API documentation is available at `/docs` (Swagger UI) when running locally.
*   **Upload Package**: `POST /packages`
*   **Get Package**: `GET /packages/{id}`
*   **Search**: `POST /packages` (Search query)
*   **Reset**: `DELETE /reset`
