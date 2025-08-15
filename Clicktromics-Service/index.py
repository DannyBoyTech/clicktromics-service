from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import logging

load_dotenv()
from src.config import ALLOW_ORIGINS

from src.model import load_admet_model
from src.mongo_client import Mongo

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await Mongo._initialize_client()
        Mongo._initialize_sync_client()
        logging.info("✅ MongoDB client initialized successfully.")
        load_admet_model()
        logging.info("✅ ADMET model loaded successfully.")
    except Exception as e:
        logging.error(f"❌ Error during application startup: {str(e)}")
    yield

app = FastAPI(
    title="Click API",
    description="Antibody Drug Conjugate and Peptide Drug Conjugate",
    version="0.0.2",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path="/clicktromics",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api import router as root_router
from src.api.click_adc import router as click_router
from src.api.click_pdc import router as click_pdc_router
from src.api.admet_ai import router as admit_router
from src.api.smiles_converter import router as smiles_converter_router
from src.api.input import router as input_router
from src.api.upload import router as upload_router
from src.api.organs import router as organs_router
from src.api.search import router as search_router
from src.auth.routes import router as auth_router

from src.api.jobs.boltz import router as boltz_router
from src.api.jobs.diffab import router as diffab_router
from src.api.jobs.homelette import router as homelette_router
from src.api.jobs.musite import router as musite_router
from src.api.jobs.gnina import router as gnina_router
from src.api.jobs.peptide_generating import router as peptide_generating_router
from src.api.jobs.blood_test import router as blood_router
from src.api.jobs.vep_ensemple import router as vep_ensemple_route
from src.api.jobs.variant_calling_bam import router as variant_calling_bam_route
from src.api.jobs.variant_calling_fastq import router as variant_calling_fastq_route
from src.api.jobs.microbiome import router as microbiome_route
from src.api.jobs.genetic_annotation import router as genetic_annotation_route
from src.api.jobs.genetic import router as genetic_route
from src.api.jobs.url_download import router as url_download_route
from src.api.jobs import router as job_api_router


app.include_router(root_router)
api_router = APIRouter(prefix="/v1")

api_router.include_router(input_router)
api_router.include_router(organs_router)
api_router.include_router(search_router)
api_router.include_router(admit_router)
api_router.include_router(smiles_converter_router)
api_router.include_router(click_router)
api_router.include_router(click_pdc_router)
api_router.include_router(upload_router)
api_router.include_router(auth_router)

job_router = APIRouter(prefix="/job")

job_router.include_router(boltz_router)
job_router.include_router(diffab_router)
job_router.include_router(homelette_router)
job_router.include_router(musite_router)
job_router.include_router(gnina_router)
job_router.include_router(peptide_generating_router)
job_router.include_router(blood_router)
job_router.include_router(vep_ensemple_route)
job_router.include_router(variant_calling_bam_route)
job_router.include_router(variant_calling_fastq_route)
job_router.include_router(microbiome_route)
job_router.include_router(genetic_annotation_route)
job_router.include_router(genetic_route)
job_router.include_router(url_download_route)
job_router.include_router(job_api_router)

api_router.include_router(job_router)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)