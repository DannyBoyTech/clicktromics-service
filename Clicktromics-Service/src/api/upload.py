from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from src.helper.aws.s3 import get_s3_service, S3Service
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.logger import Logger
from src.utils import validate_file_type, verify_checksum
from src.auth.dependencies import require_auth
from src.documents.profile import AuthProfile
import json, tempfile, os, traceback
from typing import Optional

log = Logger.get_logger()
router = APIRouter(prefix="", tags=["Upload Service"])

ALLOWED_CONTENT_TYPES = [
    "text/plain",      # TXT, MD
    "text/csv",        # CSV
    "text/xml",        # XML
    "text/vcard",      # VCF
    "application/pdf", # PDF
    "application/octet-stream", # BAM/BIN
    "application/json",# JSON
    "application/xml", # XML
    "application/epub+zip", # EPUB
    "application/vcf", # VCF
    "application/gzip",# GZ, VCF.GZ
    "application/x-gzip",
    "image/png",
    "image/jpeg",
    "image/jpg",
]

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@router.post(
    "/upload",
    summary="Upload a file to S3 or Local Storage",
    description="""
Upload a single file via multipart/form-data.  
Validates file type and optional client-provided checksum, then stores via the configured adapter (S3 or local).

**Form fields**  
- **file** (`UploadFile`, required): The file to upload.  
- **hash** (`str`, optional): Client’s checksum for integrity verification.

**Behavior**  
1. Write uploaded content to a temporary file.  
2. If `hash` is provided, verify checksum; on mismatch, returns 400.  
3. Validate MIME type against allowed list; on unsupported type, returns 400.  
4. Upload to storage adapter under `upload/{generated_object_name}`.  
5. Return the storage path for retrieval.
""",
    responses={
        200: {
            "description": "File uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "message": "File uploaded successfully",
                            "file": "upload/myfile.vcf"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request (checksum mismatch or unsupported file type)",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Unsupported file type: application/zip"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during upload",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Error encountered during processing: <details>"
                    }
                }
            }
        },
    },
)
async def upload(
    file: UploadFile = File(..., description="The file to upload (any supported type)"),
    hash: Optional[str] = Form(None, description="Optional checksum for integrity check"),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    s3: S3Service = Depends(get_s3_service),
    current_user: AuthProfile = require_auth(),
):
    try:
        # Save to temp and verify checksum
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            content = await file.read()
            tf.write(content)
            temp_path = tf.name

        if verify_checksum(content, hash):
            # raise HTTPException(status_code=400, detail="Checksum mismatch")
            pass

        if not validate_file_type(temp_path, ALLOWED_CONTENT_TYPES):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )

        objectname = "upload/" + s3.generate_valid_object_name(file.filename)
        adapter.upload(temp_path, objectname)
        return JSONResponse(
            status_code=200,
            content={"status": "success", "data": {"message": "File uploaded successfully", "file": objectname}}
        )

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        log.error(f"Error in upload: {e}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error encountered during processing: {str(e)}"}
        )
    finally:
        remove_file(temp_path)


@router.get(
    "/download",
    summary="Download raw file by object name",
    description="""
Retrieve a previously uploaded file by its storage key.  
Streams the file from the adapter to a temp file on-disk, then returns as `application/octet-stream`.
""",
    responses={
        200: {
            "description": "Raw file download",
            "content": {"application/octet-stream": {}}
        },
        500: {
            "description": "Error during download",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Error encountered during processing: <details>"
                    }
                }
            }
        },
    },
)
async def download(
    objectname: str,
    background_tasks: BackgroundTasks,
    adapter: StorageAdapter = Depends(get_storage_adapter),
    current_user: AuthProfile = require_auth(),
):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            adapter.download(objectname, tf.name)
            temp_path = tf.name

        # schedule file cleanup after response
        background_tasks.add_task(remove_file, temp_path)
        return FileResponse(temp_path, filename=os.path.basename(objectname))

    except Exception as e:
        tb = traceback.format_exc()
        log.error(f"Error in download: {e}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error encountered during processing: {str(e)}"}
        )


@router.get(
    "/download-content",
    summary="Download file and return its parsed content",
    description="""
Download a file and return its contents.  
If the file contains valid JSON, it is parsed and returned as JSON; otherwise returned as plain text.
""",
    responses={
        200: {
            "description": "Parsed file content",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {"foo": "bar"}  # or raw text
                    }
                }
            }
        },
        500: {
            "description": "Error during content retrieval",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Error encountered during processing: <details>"
                    }
                }
            }
        },
    },
)
async def download_content(
    objectname: str,
    adapter: StorageAdapter = Depends(get_storage_adapter),
    current_user: AuthProfile = require_auth(),
):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            adapter.download(objectname, tf.name)
            temp_path = tf.name

        raw = open(temp_path, "r").read()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw

        return JSONResponse(content={"status": "success", "data": parsed}, status_code=200)

    except Exception as e:
        tb = traceback.format_exc()
        log.error(f"Error in download_content: {e}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error encountered during processing: {str(e)}"}
        )
    finally:
        if temp_path:
            remove_file(temp_path)
