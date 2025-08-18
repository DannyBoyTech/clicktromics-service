from src.logger import Logger
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.request_model import AdmetPredictRequest
from src.model import get_admet_model, load_admet_model
from admet_ai import ADMETModel
from src.auth.dependencies import require_auth
from src.documents.profile import AuthProfile

log = Logger.get_logger()
router = APIRouter(prefix="/admet-ai", tags=["ADMET Model"])
selected_fields = [
    "Lipinski",
    "Lipinski_drugbank_approved_percentile",
    "QED",
    "hydrogen_bond_acceptors",
    "hydrogen_bond_donors",
    "logP",
    "molecular_weight"
]

@router.post('/predict')
def predict(
    request: AdmetPredictRequest,
    current_user: AuthProfile = require_auth()
):
    """Predict Lipinski, QED, ...etc for a specific smiles using Admet AI"""
    try:
        if not isinstance(get_admet_model(), ADMETModel):
            log.info(f"Loading model cause model did not load at lifespan")
            load_admet_model()

        log.info(f"Generate predict for smiles: {request.smiles}")
        preds = get_admet_model().predict(smiles=request.smiles) 
        filtered_preds = {key: preds[key] for key in selected_fields if key in preds}
        log.info(f"preds: {preds}")
        return JSONResponse(content={"status": "success", "data": filtered_preds}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error predict : {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)