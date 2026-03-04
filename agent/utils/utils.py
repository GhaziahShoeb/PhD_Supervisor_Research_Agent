# Production credentials from GCS Interoperability tab
import os
import threading
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

GCS_ACCESS_KEY = os.getenv("GCS_ACCESS_KEY")
GCS_SECRET_KEY = os.getenv("GCS_SECRET_KEY") 
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

import boto3
import re
from botocore.exceptions import ClientError
from deepagents.backends.protocol import BackendProtocol, WriteResult, EditResult
from deepagents.backends.utils import FileInfo, GrepMatch

class InMemoryObjectBackend(BackendProtocol):
    def __init__(self, prefix: str = ""):
        cleaned_prefix = prefix.lstrip("/")
        if cleaned_prefix and not cleaned_prefix.endswith("/"):
            cleaned_prefix = f"{cleaned_prefix}/"
        self.prefix = cleaned_prefix
        self._data = {}
        self._meta = {}
        self._lock = threading.RLock()

    def _normalize_path(self, path: str) -> str:
        relative_path = path.lstrip("/")
        return f"{self.prefix}{relative_path}"

    def _display_path(self, key: str) -> str:
        if self.prefix and key.startswith(self.prefix):
            key = key[len(self.prefix):]
        return f"/{key.rstrip('/')}"

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def ls_info(self, path: str) -> list[FileInfo]:
        prefix = self._normalize_path(path)
        if prefix and not prefix.endswith('/'):
            prefix += '/'

        results = []
        dir_names = set()
        with self._lock:
            for key, content in self._data.items():
                if not key.startswith(prefix):
                    continue
                rest = key[len(prefix):]
                if not rest:
                    continue
                if "/" in rest:
                    dir_names.add(rest.split("/", 1)[0])
                else:
                    meta = self._meta.get(key, {})
                    results.append(FileInfo(
                        path=self._display_path(key),
                        size=meta.get("size", len(content)),
                        modified_at=meta.get("modified_at", self._now()),
                    ))
        for name in sorted(dir_names):
            results.append(FileInfo(path=self._display_path(prefix + name + "/"), is_dir=True))
        return sorted(results, key=lambda x: x.path)

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        key = self._normalize_path(file_path)
        with self._lock:
            if key not in self._data:
                return f"Error: File '{file_path}' not found."
            content = self._data[key]
        lines = content.splitlines()
        subset = lines[offset : offset + limit]
        return "\n".join(f"{i+offset+1}|{line}" for i, line in enumerate(subset))

    def write(self, file_path: str, content: str) -> WriteResult:
        key = self._normalize_path(file_path)
        with self._lock:
            self._data[key] = content
            self._meta[key] = {
                "size": len(content.encode("utf-8")),
                "modified_at": self._now(),
            }
        return WriteResult(path=file_path, files_update=None)

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        key = self._normalize_path(file_path)
        with self._lock:
            if key not in self._data:
                return EditResult(error=f"File '{file_path}' not found.")
            content = self._data[key]

            count = content.count(old_string)
            if count == 0:
                return EditResult(error=f"String '{old_string}' not found.")
            if count > 1 and not replace_all:
                return EditResult(error=f"Multiple occurrences of '{old_string}' found. Use replace_all=True.")

            new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
            self._data[key] = new_content
            self._meta[key] = {
                "size": len(new_content.encode("utf-8")),
                "modified_at": self._now(),
            }
        return EditResult(path=file_path, occurrences=count, files_update=None)

    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        matches = []
        files_to_scan = self.ls_info(path or "/")
        try:
            regex = re.compile(pattern)
            with self._lock:
                for f in files_to_scan:
                    if not f.is_dir:
                        content = self._data.get(self._normalize_path(f.path), "")
                        for i, line in enumerate(content.splitlines()):
                            if regex.search(line):
                                matches.append(GrepMatch(path=f.path, line=i+1, text=line))
            return matches
        except re.error as e:
            return f"Invalid regex pattern: {str(e)}"

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        all_files = self.ls_info(path)
        regex_pattern = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
        regex = re.compile(regex_pattern)
        return [f for f in all_files if regex.search(f.path)]

class GCSObjectBackend(BackendProtocol):
    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str = "https://storage.googleapis.com",
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        prefix: str = "",
    ):
        """
        GCS uses S3-compatible credentials. 
        Get these from GCP Console -> Cloud Storage -> Settings -> Interoperability.
        """
        cleaned_prefix = prefix.lstrip("/")
        if cleaned_prefix and not cleaned_prefix.endswith("/"):
            cleaned_prefix = f"{cleaned_prefix}/"
        self.prefix = cleaned_prefix
        if aws_access_key_id is None:
            aws_access_key_id = GCS_ACCESS_KEY
        if aws_secret_access_key is None:
            aws_secret_access_key = GCS_SECRET_KEY
        if "storage.googleapis.com" in endpoint_url:
            os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
        self.s3 = boto3.resource(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.bucket = self.s3.Bucket(bucket_name)
        self.bucket_name = bucket_name

    def _normalize_path(self, path: str) -> str:
        # Remove leading slash for S3 keys
        relative_path = path.lstrip("/")
        return f"{self.prefix}{relative_path}"

    def _display_path(self, key: str) -> str:
        if self.prefix and key.startswith(self.prefix):
            key = key[len(self.prefix):]
        return f"/{key.rstrip('/')}"

    def ls_info(self, path: str) -> list[FileInfo]:
        prefix = self._normalize_path(path)
        if prefix and not prefix.endswith('/'):
            prefix += '/'
            
        results = []
        # Use delimiter to simulate directory behavior
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix, Delimiter='/'):
            # Add "Folders"
            for obj in page.get('CommonPrefixes', []):
                results.append(FileInfo(path=self._display_path(obj['Prefix']), is_dir=True))
            # Add Files
            for obj in page.get('Contents', []):
                if obj['Key'] != prefix: # Don't list the directory itself
                    results.append(FileInfo(
                        path=self._display_path(obj['Key']), 
                        size=obj['Size'], 
                        modified_at=obj['LastModified'].isoformat()
                    ))
        return sorted(results, key=lambda x: x.path)

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        key = self._normalize_path(file_path)
        try:
            obj = self.bucket.Object(key).get()
            content = obj['Body'].read().decode('utf-8')
            lines = content.splitlines()
            # Apply offset/limit and format with line numbers as per protocol
            subset = lines[offset : offset + limit]
            return "\n".join(f"{i+offset+1}|{line}" for i, line in enumerate(subset))
        except ClientError:
            return f"Error: File '{file_path}' not found."

    def write(self, file_path: str, content: str) -> WriteResult:
        key = self._normalize_path(file_path)
        try:
            # Check if exists to enforce create-only semantics if desired
            self.bucket.Object(key).put(Body=content)
            return WriteResult(path=file_path, files_update=None)
        except Exception as e:
            return WriteResult(error=str(e))

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        key = self._normalize_path(file_path)
        try:
            obj = self.bucket.Object(key).get()
            content = obj['Body'].read().decode('utf-8')
            
            count = content.count(old_string)
            if count == 0:
                return EditResult(error=f"String '{old_string}' not found.")
            if count > 1 and not replace_all:
                return EditResult(error=f"Multiple occurrences of '{old_string}' found. Use replace_all=True.")
            
            new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
            self.bucket.Object(key).put(Body=new_content)
            
            return EditResult(path=file_path, occurrences=count, files_update=None)
        except Exception as e:
            return EditResult(error=str(e))

    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        # Simple implementation: List files and scan content
        # Production tip: Use GCS Select or an external index for large buckets
        matches = []
        files_to_scan = self.ls_info(path or "/")
        try:
            regex = re.compile(pattern)
            for f in files_to_scan:
                if not f.is_dir:
                    content = self.bucket.Object(self._normalize_path(f.path)).get()['Body'].read().decode('utf-8')
                    for i, line in enumerate(content.splitlines()):
                        if regex.search(line):
                            matches.append(GrepMatch(path=f.path, line=i+1, text=line))
            return matches
        except re.error as e:
            return f"Invalid regex pattern: {str(e)}"

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        # Basic implementation: list everything and filter with regex
        all_files = self.ls_info(path)
        # Convert glob to regex
        regex_pattern = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
        regex = re.compile(regex_pattern)
        return [f for f in all_files if regex.search(f.path)]
