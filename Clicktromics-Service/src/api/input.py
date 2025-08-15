from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
import requests
import os
from src.config import RCSB_URL, DEFAULT_BUCKET_NAME
from src.logger import Logger
from src.request_model import PdbRequest
from src.helper.aws.s3 import get_s3_service, S3Service
from src.auth.dependencies import require_auth
from src.documents.profile import AuthProfile

log = Logger.get_logger()
router = APIRouter(
    prefix="/input",
    tags=["Input"]
)

@router.post("/pdb_id/")
async def download_pdb_by_id(
    request: PdbRequest,
    s3: S3Service = Depends(get_s3_service),
    current_user: AuthProfile = require_auth()
):
    """Download PDB file from rcsb.org by providing PDB ID"""
    
    if not request.pdb_id:
        return JSONResponse(content={"status": "error", "message": "PDB ID is required"}, status_code=400)

    try:
        pdb_id = request.pdb_id
        pdb_url = f"{RCSB_URL}{pdb_id}.pdb"

        log.info(f"Downloads from {RCSB_URL}")
        response = requests.get(pdb_url)
        if response.status_code != 200:
            return JSONResponse(status_code=404, content={"status": "error", "message": f"PDB file {pdb_id} not found on RCSB PDB"})

        response_data = response.content
        filename = f"{pdb_id}.pdb"
        file_path = f"output_{pdb_id}.pdb"

        with open(file_path, "wb") as f:
            f.write(response_data)

        with open(file_path, "rb") as f:
            objectname = "input/" + s3.generate_valid_object_name(filename)
            s3.upload_file(f, DEFAULT_BUCKET_NAME, objectname)
            url = s3.generate_presigned_url(DEFAULT_BUCKET_NAME, objectname)

        os.remove(file_path)
        result = {
            "message": f"PDB file {filename} has been downloaded successfully",
            "pdp_file_path": str(url)
        }
        return JSONResponse(content={"status": "success", "data": result}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error download_pdb_by_id: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)


@router.post("/upload/")
async def upload_pdb_file(
    file: UploadFile = File(...),
    s3: S3Service = Depends(get_s3_service),
    current_user: AuthProfile = require_auth()
):
    """Upload PDB file and save it in S3 to use it later with diffab"""
    try:
        objectname = "input/" + s3.generate_valid_object_name(file. filename)
        s3.upload_file(file, DEFAULT_BUCKET_NAME, objectname)
        url = s3.generate_presigned_url(DEFAULT_BUCKET_NAME, objectname)

        result = {
            "message": f"PDB file {file.filename} has been uploaded successfully",
            "pdp_file_path": str(url)
        }
        return JSONResponse(content={"status": "success", "data": result}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error upload_pdb_file: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)