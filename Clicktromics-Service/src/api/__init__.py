from fastapi import APIRouter
from src.logger import Logger

router = APIRouter(prefix="", tags=["Root Router"])
log = Logger.get_logger()

@router.get("/")
def root():
    return {"message": "API is running"}