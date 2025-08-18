from fastapi import HTTPException, APIRouter, Depends
from fastapi.responses import JSONResponse
from src.logger import Logger
from src.request_model import ClickADCRequest
from src.config import LINKERS, SMART_REACTION, GLYCAN_LINKER, GLYCANS
from src.helper.click import ClickDrug, ClickSPACC
from src.auth.dependencies import require_user_context
from src.documents.profile import AuthProfile
import random

logger = Logger.get_logger()
router = APIRouter(prefix="/click", tags=["Click Chemistry ADC"])

@router.post("/adc")
async def click_generate(
    request: ClickADCRequest,
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
            # elif request.smiles:
            #     drug = DrugDocument(chem_smiles=request.smiles)
            # else:
            #     return JSONResponse(content={"status": "error", "message": "drugbankId and smiles are empty"}, status_code=400)   
            
            clicked_drug = ClickDrug(smiles=request.smiles,linkers=LINKERS)
            glycanlinker_key, glycanlinker_value = random.choice(list(GLYCAN_LINKER.items()))
            glycan_key, glycan_value = random.choice(list(GLYCANS.items()))
            logger.info(f"clicked_drug: {clicked_drug}")
            spacc = ClickSPACC(ComplexDrug=clicked_drug, Glycan=glycan_value, GlycanLinker=glycanlinker_value, smart_reaction=SMART_REACTION['SPACC'])
        
            if not spacc:
                raise HTTPException(status_code=500, detail="Failed to generate SPACC payload")
            
            if not clicked_drug:
                raise HTTPException(status_code=500, detail="Failed to generate ClickDrug object")

            res = {
                "Glycan": {
                    glycan_key: glycan_value
                },
                "Glycan-Linker":{
                    glycanlinker_key: glycanlinker_value
                },
                "payload": spacc,
                "Linker": clicked_drug["Linker_name"]
            }
        except Exception as e:
            logger.error(f"❌ Clickable reaction failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Clickable reaction failed: {str(e)}")

        response_data =  {
            "message": "Click process completed",
            "output": res
        }   

        return JSONResponse(content={"status": "success", "data": response_data}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        logger.error(f"Error click_generate: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)