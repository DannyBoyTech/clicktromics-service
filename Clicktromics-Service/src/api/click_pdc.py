from fastapi import HTTPException, APIRouter, Depends
from fastapi.responses import JSONResponse
from src.logger import Logger
from src.request_model import ClickPDCRequest
from src.helper.click import ClickPeptide
from src.auth.dependencies import require_user_context
from src.documents.profile import AuthProfile

logger = Logger.get_logger()
router = APIRouter(prefix="/click", tags=["Click Chemistry PDC"])

@router.post("/pdc")
async def click_generate(
    request: ClickPDCRequest,
    current_user: AuthProfile = require_user_context()
):
    """Submit a SMILES string for a drug or peptide or a drugbankid, and the result will be a payload"""
  
    try:
        try:
            if request.drugbankId:
                pass
                # logger.info(request.drugbankId)
                # drug = await drugrepo.find_by_id(request.drugbankId)
                # logger.info(drug)
                # if not drug:
                #     return JSONResponse(content={"status": "error", "message": f"drugbankId {request.drugbankId} do not exist"}, status_code=404)   

            linker_peptide_smiles: str = "C[C](NC(=O)[C](NC(=O)CCOCCOCCOCCOCCN1C(=O)CC(SCCOCCOCCOCC)C1=O)C(C)C)C(=O)Nc2ccc(COC(*)=O)cc2"
            smiles = ClickPeptide(request.target_peptide_smiles , request.peptide_smiles, linker_peptide_smiles, request.linker_target_peptide_smiles)

        except Exception as e:
            logger.error(f"❌ Clickable reaction failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Clickable reaction failed: {str(e)}")

        response_data =  {
            "message": "Click process completed",
            "smiles": smiles
        }   

        return JSONResponse(content={"status": "success", "data": response_data}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        logger.error(f"Error click_generate: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)