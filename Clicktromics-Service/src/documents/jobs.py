from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, timezone
from enum import Enum
from src.utils import generate_unique_job_id


class JobTypeEnum(str, Enum):
    HOMELETTE = "homelette"
    MUSITE = "musite"
    GNINA = "gnina"
    DIFFAB = "diffab"
    PEPTIDE = "peptide_generating"
    BOLTZ = "boltz"
    VC_MATCHING = "variant_calling_matching"
    VEP_ENSEMBLE = "vep_ensemple"
    DISVAR = "disvar"
    BLOOD_TEST = "blood_test"
    MICROBIOME = "microbiome"
    ANNOTATION = "annotation"
    GENETIC = "genetic"
    URL_DOWNLOAD = "url_download"
    BAM_PROCESSING = "bam_processing"
    FASTQ_PROCESSING = "fastq_processing"
    GENETIC_ANNOTATION = "genetic_annotation"
    GAN = "gan"

class JobStatusEnum(str, Enum):
    PENDING = 'PENDING'
    RUNNABLE = 'RUNNABLE'
    STARTING = 'STARTING'
    RUNNING = 'RUNNING'
    CANCELING = 'CANCELING'
    TERMINATING = 'TERMINATING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


class JobType(BaseModel):
    name: JobTypeEnum = Field(..., description="Job type enum wrapper")

    class Config:
        arbitrary_types_allowed = True

class JobDocument(BaseModel):
    status: str = Field(JobStatusEnum.PENDING.value, description="Job execution status")
    task_id: Optional[str] = Field(None, description="Celery identifier")
    batch_id: Optional[str] = Field(None, description="AWS_Batch identifier")
    job_id: str = Field(default_factory=lambda: generate_unique_job_id(), description="Job identifier")
    inputs: Optional[Dict] = Field(None, description="Job input parameters")
    outputs: Optional[Dict] = Field({"files":[]}, description="Job output data")
    type: Optional[JobType] = Field(None, description="Type of job")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    user_email: Optional[str] = Field(None, description="Email of the user who owns the job")
    error_message: Optional[str] = Field(None, description="Message that shows way job fail")

    class Config:
        arbitrary_types_allowed = True

    @field_serializer("created_at")
    def serialize_created_at(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format for created_at
    
    @field_serializer("updated_at")
    def serialize_updated_at(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format for updated_at