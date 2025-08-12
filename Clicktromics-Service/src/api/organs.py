import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.logger import Logger 
from pathlib import Path
from src.config import root_directory
from src.utils import transform_keys

log = Logger.get_logger()
router = APIRouter(prefix="/organs", tags=["Fetch organs list"])

# Preload data once at import time
json_file_path = Path(root_directory) / "dataset" / "organs.json"
organs_data = None

try:
    if not json_file_path.exists():
        raise FileNotFoundError(f"JSON file not found at {json_file_path}")
    
    with json_file_path.open("r") as file:
        organs_data = json.load(file)
        organs_data = transform_keys(organs_data)
    log.info("Organs data loaded successfully on startup.")
except Exception as e:
    organs_data = None
    log.error(f"Failed to load organs data on startup: {e}")

@router.get("")
async def fetch_organs():
    if organs_data is None:
        raise HTTPException(status_code=500, detail="Organs data not available")
    
    log.info("Successfully fetched organs data from memory")
    return JSONResponse(content={"status": "success", "data": organs_data}, status_code=200)
