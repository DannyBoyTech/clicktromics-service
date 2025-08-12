
import os
import requests
from abc import ABC, abstractmethod
from src.logger import Logger
from src.config import USE_LOCAL_STORAGE, LOCAL_STORAGE_PATH, DEFAULT_BUCKET_NAME

logger = Logger.get_logger()

class StorageAdapter(ABC):
    @abstractmethod
    def download(self, source: str, dest_path: str) -> None:
        ...

    @abstractmethod
    def upload(self, src_path: str, dest: str) -> None:
        ...


class S3Adapter(StorageAdapter):
    def __init__(self, bucket: str):
        import boto3, botocore
        self.s3 = boto3.client('s3')
        self.bucket = bucket

    def download(self, object_key: str, dest_path: str) -> None:
        logger.info(f"S3Adapter: Downloading s3://{self.bucket}/{object_key} → {dest_path}")
        try:
            self.s3.download_file(self.bucket, object_key, dest_path)
        except Exception as e:
            logger.error(f"S3 download error: {e}")
            raise

    def upload(self, src_path: str, object_key: str) -> None:
        logger.info(f"S3Adapter: Uploading {src_path} → s3://{self.bucket}/{object_key}")
        try:
            self.s3.upload_file(src_path, self.bucket, object_key)
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            raise


class LocalAdapter(StorageAdapter):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def download(self, filename: str, dest_path: str) -> None:
        src = os.path.join(self.base_dir, filename)
        logger.info(f"LocalAdapter: Copying {src} → {dest_path}")
        if not os.path.exists(src):
            raise FileNotFoundError(f"Local file not found: {src}")
        with open(src, "rb") as sf, open(dest_path, "wb") as df:
            df.write(sf.read())

    def upload(self, src_path: str, filename: str) -> None:
        dst = os.path.join(self.base_dir, filename)
        dir_path = os.path.dirname(dst)
        os.makedirs(dir_path, exist_ok=True)

        logger.info(f"LocalAdapter: Copying {src_path} → {dst}")
        with open(src_path, "rb") as sf, open(dst, "wb") as df:
            df.write(sf.read())


class HttpAdapter(StorageAdapter):
    """Only supports download via HTTP(S)."""
    def download(self, url: str, dest_path: str) -> None:
        logger.info(f"HttpAdapter: Downloading {url} → {dest_path}")
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(8_192):
                f.write(chunk)

    def upload(self, src_path: str, dest: str) -> None:
        raise NotImplementedError("HttpAdapter cannot upload")


class FallbackAdapter(StorageAdapter):
    """
    Tries primary first; on download‐error falls back to download_fallback;
    on upload‐error falls back to upload_fallback.
    """
    def __init__(
        self,
        primary: StorageAdapter,
        download_fallback: StorageAdapter,
        upload_fallback: StorageAdapter
    ):
        self.primary = primary
        self.download_fallback = download_fallback
        self.upload_fallback = upload_fallback

    def download(self, source: str, dest_path: str) -> None:
        try:
            self.primary.download(source, dest_path)
        except Exception as e:
            logger.warning(f"Primary download failed ({e}), trying fallback…")
            self.download_fallback.download(source, dest_path)

    def upload(self, src_path: str, dest: str) -> None:
        try:
            self.primary.upload(src_path, dest)
        except Exception as e:
            logger.warning(f"Primary upload failed ({e}), trying fallback…")
            self.upload_fallback.upload(src_path, dest)


def get_storage_adapter() -> StorageAdapter:
    """Builds a composite adapter that covers:
       • primary = S3 or local (configurable by USE_LOCAL_STORAGE)
       • download-fallback = HTTP GET 
       • upload-fallback = local disk
    """
    use_local = USE_LOCAL_STORAGE.lower() in ("1", "true", "yes")
    if use_local:
        primary = LocalAdapter(LOCAL_STORAGE_PATH)
        download_fallback = S3Adapter(DEFAULT_BUCKET_NAME)
        upload_fallback = S3Adapter(DEFAULT_BUCKET_NAME)
    else:
        primary = S3Adapter(DEFAULT_BUCKET_NAME)
        download_fallback = LocalAdapter(LOCAL_STORAGE_PATH)
        upload_fallback = LocalAdapter(LOCAL_STORAGE_PATH)

    return FallbackAdapter(primary, download_fallback, upload_fallback)