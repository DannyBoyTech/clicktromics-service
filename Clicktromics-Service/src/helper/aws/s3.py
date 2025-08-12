import re, os, uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from src.config import AWS_ACCESS_KEY, AWS_SECRET_KEY
from datetime import datetime, timezone
from src.logger import Logger
from typing import Union, IO
import mimetypes
import asyncio
from starlette.datastructures import UploadFile as StarletteUploadFile

log = Logger.get_logger()

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )

    def upload_file(self, file: Union[UploadFile, IO[bytes]], bucket_name: str, object_name: str):
        """
        Upload a file to an S3 bucket.
        
        Args:
            file: Either a FastAPI UploadFile or a file-like object (e.g., from open())
            bucket_name: Name of the S3 bucket
            object_name: S3 object key (file path in bucket)
        """
        try:
             # Determine file object and content type
            if isinstance(file, (UploadFile, StarletteUploadFile)):
                if asyncio.iscoroutine(file.file):
                    raise ValueError("file.file is a coroutine — did you forget to await file.read() and wrap it?")

                file_obj = file.file
                content_type = file.content_type or 'application/octet-stream'
            else:
                file_obj = file
                # Infer content type from object_name if possible
                content_type = mimetypes.guess_type(object_name)[0] or 'application/octet-stream'
                
                # Ensure file is at the start
                file_obj.seek(0)
                
            self.s3_client.upload_fileobj(file_obj, bucket_name, object_name, ExtraArgs={'ContentType': content_type})
        except ClientError as e:
            log.error(f"Failed to upload file to S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")
        except Exception as e:
            log.error(f"Unexpected error during file upload: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
        
    def generate_presigned_url(self, bucket_name: str, object_name: str, expiration: int = 604800):
        """
        Generate a pre-signed URL for downloading a file from S3.
        
        Args:
            bucket_name: Name of the S3 bucket
            object_name: S3 object key
            expiration: Time in seconds for the URL to remain valid (default: 1 hour)
        
        Returns:
            str: Pre-signed URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate pre-signed URL: {str(e)}")

    def generate_valid_object_name(self, original_name: str, use_unique_id: bool = True) -> str:
        """
        Generate a valid S3 object name from the original file name.
        
        Args:
            original_name: Original file name (e.g., "My File!.txt")
            use_unique_id: Whether to append a unique identifier (default: True)
        
        Returns:
            str: Valid S3 object name (e.g., "my_file_20250414t123456.txt" or "my_file.txt")
        """
        # Extract base name and extension
        base_name, ext = os.path.splitext(original_name)
        
        # Replace invalid characters with underscores, convert to lowercase
        valid_name = re.sub(r'[^a-zA-Z0-9._-]', '_', base_name).lower()
        
        # Remove multiple consecutive underscores
        valid_name = re.sub(r'_+', '_', valid_name).strip('_')
        
        # Ensure the name isn't empty
        if not valid_name:
            valid_name = "file"
        
        # Append unique identifier if requested
        if use_unique_id:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            unique_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
            valid_name = f"{valid_name}_{unique_id}"
        
        # Reattach extension (lowercase)
        return f"{valid_name}{ext.lower()}"

    def check_object_existence(self, bucket_name, object_key):
        try:
            s3_res = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
        except ClientError as e:
            match int(e.response['Error']['Code']):
                case 400:
                    raise Exception("services:aws:s3:check_object_existence::s3 request credentials error")
                case 404:
                    return False
                case _:
                    raise Exception("services:aws:s3:check_object_existence::s3 unknown error")
            
        return True



def get_s3_service():
    return S3Service()


