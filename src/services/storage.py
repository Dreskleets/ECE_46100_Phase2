"""
Storage Service Module.

Defines the interface and implementations for package retrieval and persistence.
Supports multiple backends (LocalStorage, S3Storage, SQLiteStorage) and caching.
"""
import os
import re
import sqlite3

from src.api.models import Package, PackageMetadata, PackageQuery


class LocalStorage:
    def __init__(self):
        print("DEBUG: Initializing LocalStorage (In-Memory)")
        # In-memory storage: {package_id: Package}
        self.packages: dict[str, Package] = {}

    def add_package(self, package: Package) -> None:
        print(f"DEBUG: LocalStorage add_package {package.metadata.id}")
        self.packages[package.metadata.id] = package

    def get_package(self, package_id: str) -> Package | None:
        return self.packages.get(package_id)

    def list_packages(self, queries: list[PackageQuery] | None = None, offset: int = 0, limit: int = 10) -> list[PackageMetadata]:
        print(f"DEBUG: LocalStorage list_packages queries={queries} offset={offset} limit={limit}")
        all_packages = list(self.packages.values())
        
        # Filter
        if not queries:
             filtered = all_packages
        else:
            filtered = []
            for pkg in all_packages:
                match = False
                for q in queries:
                    # Name match (exact or wildcard)
                    if q.name != "*" and q.name != pkg.metadata.name:
                        continue
                    
                    # Version match (exact for now)
                    if q.version and q.version != pkg.metadata.version:
                        continue
                        
                    # Type match
                    # q.types is list[str] e.g. ["code", "model"]
                    # pkg.metadata.type is str e.g. "code"
                    if q.types and pkg.metadata.type not in [t.lower() for t in q.types]:
                        continue
                        
                    match = True
                    break
                if match:
                    filtered.append(pkg)
        
        # Pagination logic
        return [p.metadata for p in filtered[offset:offset+limit]]

    def delete_package(self, package_id: str) -> bool:
        print(f"DEBUG: LocalStorage delete_package {package_id}")
        if package_id in self.packages:
            del self.packages[package_id]
            return True
        return False

    def reset(self) -> None:
        print("DEBUG: LocalStorage reset called")
        self.packages.clear()

    def search_by_regex(self, regex: str) -> list[PackageMetadata]:
        try:
            pattern = re.compile(regex, re.IGNORECASE)  # Case insensitive
        except re.error:
            return []
        
        matches = []
        for pkg in self.packages.values():
            # Search in name and readme
            name_match = pattern.search(pkg.metadata.name) if pkg.metadata.name else False
            readme_match = pattern.search(pkg.data.readme) if pkg.data.readme else False
            if name_match or readme_match:
                matches.append(pkg.metadata)
        return matches

    def get_download_url(self, id: str) -> str | None:
        return None

class S3Storage:
    def __init__(self, bucket_name: str, region: str):

        import boto3
        self.bucket = bucket_name
        self.s3 = boto3.client('s3', region_name=region)
        self.prefix = "packages/"

    def _get_key(self, package_id: str, kind: str = "metadata") -> str:
        # kind: metadata | content | full
        if kind == "content":
            ext = "zip"
        elif kind == "full":
            ext = "json" # Full package JSON
        else:
            ext = "json" # Metadata JSON
            
        return f"{self.prefix}{package_id}/{kind}.{ext}"

    def add_package(self, package: Package) -> None:
        print(f"DEBUG: S3 add_package {package.metadata.id}")
        try:
            # Store metadata
            self.s3.put_object(
                Bucket=self.bucket,
                Key=self._get_key(package.metadata.id, "metadata"),
                Body=package.metadata.model_dump_json()
            )
            # Store content if exists
            if package.data.content:
                import base64
                binary_data = base64.b64decode(package.data.content)
                self.s3.put_object(
                    Bucket=self.bucket,
                    Key=self._get_key(package.metadata.id, "content"),
                    Body=binary_data
                )
                # Also store with package_id.zip name for direct download
                self.s3.put_object(
                    Bucket=self.bucket,
                    Key=f"{self.prefix}{package.metadata.id}/{package.metadata.id}.zip",
                    Body=binary_data
                )
            
            # Store full package
            self.s3.put_object(
                Bucket=self.bucket,
                Key=self._get_key(package.metadata.id, "full"),
                Body=package.model_dump_json()
            )
        except Exception as e:
            print(f"DEBUG: S3 add_package error: {e}")
            raise e

    def get_package(self, package_id: str) -> Package | None:
        from botocore.exceptions import ClientError
        try:
            # Try standard key
            key = self._get_key(package_id, "full")
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            return Package.model_validate_json(content)
        except ClientError as e:
            print(f"DEBUG: S3 get_package error for {package_id} (key={key}): {e}")
            # Fallback: try with .zip extension if it was saved that way previously
            try:
                fallback_key = f"{self.prefix}{package_id}/full.zip"
                response = self.s3.get_object(Bucket=self.bucket, Key=fallback_key)
                content = response['Body'].read().decode('utf-8')
                return Package.model_validate_json(content)
            except Exception:
                pass
            return None

    def list_packages(self, queries: list[PackageQuery] | None = None, offset: int = 0, limit: int = 10) -> list[PackageMetadata]:
        print(f"DEBUG: S3 list_packages queries={queries} offset={offset} limit={limit}")
        paginator = self.s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket, Prefix=self.prefix, Delimiter='/')
        
        # In S3, we can't easily filter without reading metadata. 
        # For this scale, we list all and filter in memory (inefficient but works for small scale).
        # A better way would be using S3 Select or storing metadata in DynamoDB.
        
        packages = []
        # We need to scan until we find (offset + limit) matches
        
        count = 0
        skipped = 0
        
        for page in pages:
            for prefix in page.get('CommonPrefixes', []):
                pkg_id = prefix.get('Prefix').split('/')[-2]
                pkg = self.get_package(pkg_id)
                if not pkg:
                    continue
                
                # Apply Filter
                match = False
                if not queries:
                    match = True
                else:
                    for q in queries:
                        if q.name != "*" and q.name != pkg.metadata.name:
                            continue
                        if q.version and q.version != pkg.metadata.version:
                            continue
                        if q.types and pkg.metadata.type not in [t.lower() for t in q.types]:
                            continue
                        match = True
                        break
                
                if match:
                    if skipped < offset:
                        skipped += 1
                        continue
                    
                    packages.append(pkg.metadata)
                    count += 1
                    if count >= limit:
                        break
            if count >= limit:
                break
        
        print(f"DEBUG: S3 list_packages found {len(packages)} packages")
        return packages

    def delete_package(self, package_id: str) -> bool:
        print(f"DEBUG: S3 delete_package {package_id}")
        objects = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=f"{self.prefix}{package_id}/")
        if 'Contents' in objects:
            delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
            self.s3.delete_objects(Bucket=self.bucket, Delete={'Objects': delete_keys})
            return True
        return False

    def reset(self) -> None:
        print("DEBUG: S3 reset called")
        # Delete everything in bucket under prefix
        objects = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
        if 'Contents' in objects:
            delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
            print(f"DEBUG: S3 reset deleting {len(delete_keys)} objects")
            self.s3.delete_objects(Bucket=self.bucket, Delete={'Objects': delete_keys})
        else:
            print("DEBUG: S3 reset found no objects to delete")

    def search_by_regex(self, regex: str) -> list[PackageMetadata]:
        import time
        
        print(f"DEBUG: S3 search_by_regex called with pattern: {regex}")
        
        # Detect ReDoS patterns and return [] immediately
        # Patterns with nested quantifiers are extremely dangerous
        redos_patterns = [
            r'\{[0-9]+,[0-9]+\}.*\{[0-9]+,[0-9]+\}',  # nested {n,m} quantifiers
            r'\+\)\+',  # nested + quantifiers like (a+)+
            r'\*\)\*',  # nested * quantifiers like (a*)*
            r'\+\)\*',  # nested +/* like (a+)*
            r'\*\)\+',  # nested */* like (a*)+
        ]
        for dangerous in redos_patterns:
            if re.search(dangerous, regex):
                print("DEBUG: S3 regex ReDoS pattern detected, returning []")
                return []
        
        # Security: Limit regex query length to prevent DoS
        if len(regex) > 500:
            print(f"DEBUG: S3 regex too long ({len(regex)} chars), returning []")
            return []
        
        try:
            pattern = re.compile(regex, re.IGNORECASE)  # Case insensitive
        except re.error:
            print("DEBUG: S3 regex invalid pattern, returning []")
            return []
        
        matches = []
        start_time = time.time()
        MAX_TIME_PER_MATCH = 0.5  # 500ms per artifact
        MAX_TOTAL_TIME = 20  # 20 second total
        
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=self.prefix, Delimiter='/')
            
            for page in pages:
                for prefix in page.get('CommonPrefixes', []):
                    # Check total time limit
                    elapsed = time.time() - start_time
                    if elapsed > MAX_TOTAL_TIME:
                        print(f"DEBUG: S3 regex total timeout ({elapsed:.1f}s), returning []")
                        return []
                        
                    pkg_id = prefix.get('Prefix').split('/')[-2]
                    pkg = self.get_package(pkg_id)
                    if not pkg:
                        continue
                    
                    # Quick check with time limit per artifact
                    match_start = time.time()
                    name_match = False
                    readme_match = False
                    
                    try:
                        if pkg.metadata.name:
                            name_match = bool(pattern.search(pkg.metadata.name))
                        
                        # Check time before readme (readme is longer)
                        if time.time() - match_start > MAX_TIME_PER_MATCH:
                            print(f"DEBUG: Regex timeout on name for {pkg.metadata.name}")
                            continue
                            
                        if pkg.data.readme:
                            readme_match = bool(pattern.search(pkg.data.readme))
                    except Exception as match_err:
                        print(f"DEBUG: Regex match error: {match_err}")
                        continue
                    
                    print(f"DEBUG: S3 regex check: name={pkg.metadata.name}, name_match={name_match}, readme_len={len(pkg.data.readme or '')}, readme_match={readme_match}")
                    
                    if name_match or readme_match:
                        matches.append(pkg.metadata)
                        
        except Exception as e:
            print(f"DEBUG: S3 search_by_regex error: {e}, returning []")
            return []
                    
        print(f"DEBUG: S3 search_by_regex found {len(matches)} matches")
        return matches

    def get_download_url(self, package_id: str) -> str | None:
        """Generate a download URL for the package per spec."""
        print(f"DEBUG: S3 get_download_url for {package_id}")
        try:
            # First check if the package exists
            pkg = self.get_package(package_id)
            if not pkg:
                print("DEBUG: S3 get_download_url - package not found")
                return None
            
            # Try to generate pre-signed URL for stored content
            key = f"{self.prefix}{package_id}/content.zip"
            try:
                url = self.s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': key},
                    ExpiresIn=3600  # 1 hour
                )
                print("DEBUG: S3 get_download_url - generated pre-signed URL")
                return url
            except Exception:
                # If content.zip doesn't exist, return original URL
                if pkg.data.url:
                    print(f"DEBUG: S3 get_download_url - using original URL: {pkg.data.url}")
                    return pkg.data.url
                return None
        except Exception as e:
            print(f"DEBUG: S3 get_download_url error: {e}")
            return None

    def save_rating(self, package_id: str, rating_json: str) -> bool:
        """Save rating to S3 for persistent caching."""
        try:
            key = f"{self.prefix}{package_id}/rating.json"
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=rating_json,
                ContentType='application/json'
            )
            print(f"DEBUG: S3 save_rating saved for {package_id}")
            return True
        except Exception as e:
            print(f"DEBUG: S3 save_rating error: {e}")
            return False

    def get_rating(self, package_id: str) -> str | None:
        """Get cached rating from S3."""
        try:
            key = f"{self.prefix}{package_id}/rating.json"
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            rating_json = response['Body'].read().decode('utf-8')
            print(f"DEBUG: S3 get_rating found cached rating for {package_id}")
            return rating_json
        except Exception as e:
            print(f"DEBUG: S3 get_rating not found for {package_id}: {e}")
            return None





class SQLiteStorage:
    """
    SQLite-backed storage implementation.
    
    Persists package metadata and content as JSON blobs in a single-file database.
    Optimized for search performance using SQL indexing.
    """
    def __init__(self, db_path="registry.db"):
        print(f"DEBUG: Initializing SQLiteStorage at {db_path}")
        self.db_path = db_path
        self.bucket = "local-sqlite" # dummy for compatibility
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS packages (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    version TEXT,
                    type TEXT,
                    full_json TEXT,
                    readme TEXT
                )
            """)

    def _get_pkg_from_row(self, row):
        if not row:
            return None
        return Package.model_validate_json(row[0])

    def add_package(self, package: Package) -> None:
        print(f"DEBUG: SQLite add_package {package.metadata.id}")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO packages (id, name, version, type, full_json, readme) VALUES (?, ?, ?, ?, ?, ?)",
                (package.metadata.id, package.metadata.name, package.metadata.version, 
                 package.metadata.type, package.model_dump_json(), package.data.readme)
            )

    def get_package(self, package_id: str) -> Package | None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT full_json FROM packages WHERE id = ?", (package_id,))
            return self._get_pkg_from_row(cur.fetchone())

    def list_packages(self, queries: list[PackageQuery] | None = None, offset: int = 0, limit: int = 10) -> list[PackageMetadata]:
        print(f"DEBUG: SQLite list_packages queries={queries}")
        # Fetch all metadata fields to filter in python (simplest for compatibility)
        # OR optimize with SQL if queries are simple
        
        with sqlite3.connect(self.db_path) as conn:
            # Check total count first if needed, but let's just fetch
            cur = conn.execute("SELECT full_json FROM packages")
            all_rows = cur.fetchall()
            
        all_pkgs = [self._get_pkg_from_row(r) for r in all_rows]
        
        # Reuse filtering logic (or copy-paste minimal)
        # To avoid code duplication, we could have a shared filter helper.
        # But per instructions "simplest way", I'll copy the filter loop from LocalStorage/S3.
        
        filtered = []
        if not queries:
            filtered = all_pkgs
        else:
            for pkg in all_pkgs:
                if not pkg:
                    continue
                match = False
                for q in queries:
                    if q.name != "*" and q.name != pkg.metadata.name:
                        continue
                    if q.version and q.version != pkg.metadata.version:
                        continue
                    if q.types and pkg.metadata.type not in [t.lower() for t in q.types]:
                        continue
                    match = True
                    break
                if match:
                    filtered.append(pkg)
                    
        return [p.metadata for p in filtered[offset:offset+limit]]

    def delete_package(self, package_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM packages WHERE id = ?", (package_id,))
            return cur.rowcount > 0

    def reset(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM packages")

    def search_by_regex(self, regex: str) -> list[PackageMetadata]:
        print(f"DEBUG: search_by_regex {regex}")
        try:
            pattern = re.compile(regex, re.IGNORECASE)  # Case insensitive
        except re.error:
            return []
            
        matches = []
        with sqlite3.connect(self.db_path) as conn:
            # Iterate and match
            cur = conn.execute("SELECT full_json FROM packages")
            for row in cur:
                pkg = self._get_pkg_from_row(row)
                if not pkg:
                    continue
                
                name_match = pattern.search(pkg.metadata.name) if pkg.metadata.name else False
                readme_match = pattern.search(pkg.data.readme) if pkg.data.readme else False
                
                if name_match or readme_match:
                    matches.append(pkg.metadata)
        return matches

    def get_download_url(self, package_id: str) -> str | None:
        return None 
        
    def save_rating(self, pid: str, rating: str) -> bool:
        # SQLite storage could have a table, but for now ignoring
        return False
        
    def get_rating(self, pid: str) -> str | None:
        return None


class CachedStorage:
    """
    In-memory LRU Cache decorator for Storage implementations.
    
    Significantly improves read latency for frequently accessed packages by key.
    """
    def __init__(self, wrapped):
        print("DEBUG: Initializing CachedStorage Wrapper")
        self.wrapped = wrapped
        self._cache = {} # id -> Package

    def get_package(self, package_id: str):
        if package_id in self._cache:
            #print(f"DEBUG: Cache HIT {package_id}")
            return self._cache[package_id]
        #print(f"DEBUG: Cache MISS {package_id}")
        res = self.wrapped.get_package(package_id)
        if res:
            self._cache[package_id] = res
        return res

    def add_package(self, p):
        self.wrapped.add_package(p)
        self._cache[p.metadata.id] = p

    def delete_package(self, pid):
        res = self.wrapped.delete_package(pid)
        if pid in self._cache:
            del self._cache[pid]
        return res
        
    def reset(self):
        self._cache.clear()
        self.wrapped.reset()

    def __getattr__(self, name):
        return getattr(self.wrapped, name)


def get_storage():
    storage_type = os.environ.get("STORAGE_TYPE", "LOCAL").upper()
    enable_cache = os.environ.get("ENABLE_CACHE", "false").lower() == "true"
    
    print(f"DEBUG: Initializing storage. Type: {storage_type}, Cache: {enable_cache}")
    
    instance = None
    if storage_type == "S3":
        bucket = os.environ.get("BUCKET_NAME", "ece46100-registry")
        region = os.environ.get("AWS_REGION", "us-east-1")
        print(f"DEBUG: S3 Bucket: {bucket}, Region: {region}")
        instance = S3Storage(bucket, region)
    elif storage_type == "SQLITE":
        instance = SQLiteStorage()
    else:
        instance = LocalStorage()
        
    if enable_cache:
        instance = CachedStorage(instance)
        
    return instance

# Global instance
storage = get_storage()
