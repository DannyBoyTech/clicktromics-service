from fastapi import APIRouter, Query, Depends, HTTPException

import os
from fastapi.responses import JSONResponse
from src.documents.jobs import JobDocument, JobTypeEnum, JobStatusEnum
from src.repo.jobs import JobRepo
from celery.result import AsyncResult
from celery import states
from src.celery_client import Celery
from typing import List
from src.helper.aws.batch import terminate_job
from src.logger import Logger
from src.request_model import JobSuccessResponse, JobErrorResponse, JobData
from src.auth.dependencies import require_user_context
from src.documents.profile import AuthProfile
import json

log = Logger.get_logger()
router = APIRouter(prefix="", tags=["Job Management"])

@router.get("/info",
    response_model=JobSuccessResponse,
    responses={
        200: {"description": "Job information retrieved successfully", "model": JobSuccessResponse},
        400: {"description": "Bad request", "model": JobErrorResponse},
        500: {"description": "Internal server error", "model": JobErrorResponse}
    },
    summary="Get job type information",
    description="""
Get information about a specific job type.

### Query Parameters:
- **job_type** (`JobTypeEnum`, required): Name of the job type to get info for.

### Behavior:
- Retrieves information about the specified job type.
- Returns details about supported formats, estimated duration, and resource requirements.

### Responses:
- `200 OK`: Job information retrieved successfully.
- `400 Bad Request`: Invalid job type parameter.
- `500 Internal Server Error`: Server error during processing.
    """
)
async def get_job_info(
    job_type: JobTypeEnum = Query(..., description="Name of the job type to get info for"),
    current_user: AuthProfile = require_user_context(),
):
    """Get the information of a specific job type"""
    try:
        # This is a placeholder - implement actual job type info logic
        # In sandbox-BE, this uses PipelineFactory.create() and pipeline.get_info()
        log.info(f"Getting info for job type: {job_type}")
        
        # Return basic info for now
        info = {
            "job_type": job_type.value,
            "description": f"Information about {job_type.value} job type",
            "supported_formats": [],
            "estimated_duration": "varies",
            "resource_requirements": "GPU recommended"
        }
        
        return JobSuccessResponse(
            data=JobData(
                job_id="info",
                message=json.dumps(info)
            )
        )
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error get_job_info for job type {job_type}: {str(error_message)}")
        raise HTTPException(
            status_code=500,
            detail="Error encountered during processing. Please review the application log for detailed information"
        )

@router.get("/status/{job_id}", response_model=JobDocument)
async def get_job_status(
    job_id: str,
    repo: JobRepo = Depends(lambda: JobRepo()),
    current_user: AuthProfile = require_user_context()
):
    """Get the data of a specific job"""
    try:
        job = await repo.find_by_job_id(job_id)
        if not job:
            log.error(f"Job not found with the ID: {job_id}")
            return JSONResponse(status_code=404, content={"status": "error", "message": "Job not found"})

        return JSONResponse(content={"status": "success", "data": job.model_dump()}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error get_job_status with {job_id}: {str(error_message)}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

@router.get("/", response_model=List[JobDocument])
async def get_jobs(
    page: int = Query(0, alias="page", ge=0, description="Number of the result page"),
    batch_size: int = Query(5, ge=1, le=100, alias="batch_size", description="Number of rows in page"),
    stage_status: str = Query(None, description="Filter by current job stage status"),
    job_type: JobTypeEnum = Query(None, description="Filter by job type"),
    sort_desc: bool = Query(True, description="Sort by timestamp descending"),
    repo: JobRepo = Depends(lambda: JobRepo()),
    current_user: AuthProfile = require_user_context()
):
    """Get the data of jobs"""
    try:
        query = {}

        # Optional filter by stage.status
        if stage_status:
            query["stage.status"] = stage_status.upper()
        if job_type:
            query["type.name"] = job_type.lower()

        # Sort by timestamp
        sort_order = -1 if sort_desc else 1
        skip = page * batch_size
        results = await repo.get(query, sort_order, skip, batch_size)

        return JSONResponse(content={"status": "success", "data": [result.model_dump() for result in results]}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error get_jobs: {str(error_message)}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

@router.put("/{job_id}/cancel")
async def cancel_task(
    job_id: str,
    repo: JobRepo = Depends(lambda: JobRepo()),
    current_user: AuthProfile = require_user_context()
):
    """Cancel running task"""
    job = await repo.find_by_job_id(
        job_id
    )

    if not job:
        log.error(f"Job not found with the ID: {job_id}")
        return JSONResponse(status_code=404, content={"status": "error", "message": "Job not found"})

    task_id = job.task_id

    if not task_id:
        log.error(f"Job {job.job_id} has no task_id.")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Job has no associated task ID."}
        )

    if  job.status in [JobStatusEnum.FAILED.value, JobStatusEnum.CANCELLED.value, JobStatusEnum.SUCCEEDED.value]:
        log.error(f"Task not found or already completed")
        return JSONResponse(status_code=404, content={"status": "error", "message": "Task not found or already completed"})

    try:
        result = AsyncResult(task_id, app=Celery.get_client())
        job.status = JobStatusEnum.CANCELING.value
        await repo.update(job)

        if result.state in [states.PENDING, states.RECEIVED]:
            result.revoke(terminate=False, wait=True, timeout=10)
            log.info(f"Task with ID {task_id} revoked before execution.")

        elif result.state in [states.STARTED]:
            result.revoke(terminate=True, signal="SIGUSR1", wait=True, timeout=10)
            log.info(f"Task with ID {task_id} forcefully terminated.")
        
        job.status = JobStatusEnum.CANCELLED.value
        await repo.update(job)

        if terminate_job(job.batch_id) == None:
            raise Exception("Failed to cancel")

        log.info(f"Task with ID {job_id} canceled successfully.")
        return JSONResponse(content={"status": "success", "data": f"Task with ID {job_id} canceled successfully."}, status_code=200)

    except Exception as e:
        error_message = str(e) or "Unknown error occurred"
        log.error(f"Error in submit_job: {error_message}")
        return JSONResponse(
            content={"status": "error", "message": f"Error encountered during processing: {error_message}"},
            status_code=500,
        )