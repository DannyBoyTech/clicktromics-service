from src.logger import Logger
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
from src.request_model import SmilesRequest
from rdkit import Chem
from openbabel import pybel
import requests
from src.helper.aws.s3 import get_s3_service, S3Service
from src.utils import get_remote_file_content, generate_unique_job_id
from src.auth.dependencies import require_auth
from src.documents.profile import AuthProfile
import os, time, base64
from src.helper.click import fasta_to_peptide_smiles

log = Logger.get_logger()
router = APIRouter(prefix="/smiles-converter", tags=["Smiles Converter"])

ALLOWED_EXTENSION = ".pdb"  # Only allow PDB files

@router.post('/2d-smi')
def predict_2d_smi(
    request: SmilesRequest,
    current_user: AuthProfile = require_auth()
):
    """From SMILES string to a 2D smi data format"""
    if not request.smiles:
        log.info(f"smiles is empty, please provide valid smiles")
        return JSONResponse(content={"status": "error", "message": "smiles is empty, please provide valid smiles"}, status_code=400)
    
    try:
        smiles = request.smiles
        log.info(f"Generate smi file for smiles: {smiles}")
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError("Invalid SMILES! Could not parse SPACC into a molecule.")
        # Generate 2D MOL block from RDKit
        mol_2d = Chem.MolToMolBlock(mol)
        return JSONResponse(content={"status": "success", "data": mol_2d}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error predict_2d_smi : {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

@router.post('/3d-sdf')
def predict_3d_sdf(
    request: SmilesRequest,
    current_user: AuthProfile = require_auth()
):
    """From SMILES string to a 3D sdf data format"""
    if not request.smiles:
        log.info(f"smiles is empty, please provide valid smiles")
        return JSONResponse(content={"status": "error", "message": "smiles is empty, please provide valid smiles"}, status_code=400)
    
    try:
        smiles = request.smiles
        log.info(f"Generate smi file for smiles: {smiles}")
        mol = pybel.readstring("smi", smiles)
        if mol is None:
            raise ValueError("Invalid SMILES! Could not parse SPACC into a molecule.")
        # Generate 2D MOL block from RDKit
        mol.make3D(forcefield="mmff94", steps=1000)
        mol_3d = mol.write("sdf")
        return JSONResponse(content={"status": "success", "data": mol_3d}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error predict_3d_sdf : {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

@router.post('/from-pdb')
def predict_from_pdb_file(
    file_url: str = Form(...),
    s3: S3Service = Depends(get_s3_service),
    current_user: AuthProfile = require_auth()
):
    """Predict SMILES from a pdb file"""

    try:

        file_path = f'temp_{generate_unique_job_id()}.pdb'
        with open(file_path, "w") as f:
            f.write(get_remote_file_content(file_url))

        mol = Chem.MolFromPDBFile(file_path, removeHs=False)
        os.remove(file_path)
        
        if mol:
            smiles = Chem.MolToSmiles(mol, canonical=True)
            log.info("Canonical SMILES:", smiles)
            result = {
                "smiles": smiles
            }
        
            return JSONResponse(content={"status": "success", "data": result}, status_code=200)
        else:
            return JSONResponse(content={"status": "error", "data": "RDKit couldn't parse the PDB file."}, status_code=500)

    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error predict_from_pdb_file: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)


@router.post('/to-image')
def smiles_to_image(
    smiles: str = Form(...),
    current_user: AuthProfile = require_auth()
):
    """Get image from smarts.plus"""

    temp_image_path = None  # Initialize variable to track the temporary file path
    try:
        wait_time = 1
        max_attempts = 10
        api_key = 'iuZteMsIr4HiYjINMjTei-idaVJ9bnmxghZh6ZpOoXo'

        data = {
            "query": {
                "smarts": smiles,
                "parameters": {
                    "file_format": "png",
                    "legend_mode": 0,
                    "labels_for_atoms": False,
                    "smartstrim_active": False,
                    "visualization_mode": 0,
                    "smarts_string_into_picture": True,
                    "visualization_of_default_bonds": 0
                }
            }
        }

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }

        response = requests.post('https://api.smarts.plus/smartsView/', headers=headers, json=data)

        if response.status_code == 202:
            job_id = response.json().get('job_id')
            log.info("🕒 Waiting for image preparation...")
            for _ in range(max_attempts):
                time.sleep(wait_time)
                poll = requests.get(f'https://api.smarts.plus/smartsView/?job_id={job_id}')
                if poll.status_code == 200:
                    image_base64 = poll.json().get("result", {}).get("image")
                    if image_base64:
                        image_bytes = base64.b64decode(image_base64)
                        # Save image bytes to a temporary file
                        temp_image_path = f"temp_{generate_unique_job_id()}.png"
                        with open(temp_image_path, "wb") as image_file:
                            image_file.write(image_bytes)

                        # Return the image file as a response
                        return FileResponse(temp_image_path, media_type="image/png", filename="smarts_image.png")
            log.error("❌ Image preparation took too long.")
            return JSONResponse(content={"status": "error", "data": f"Image preparation took too long."}, status_code=500)
        elif response.status_code == 200:
            image_base64 = response.json()["result"]["image"]
            image_bytes = base64.b64decode(image_base64)
        else:
            log.error("❌ Error:", response.status_code, response.text)
            return JSONResponse(content={"status": "error", "data": f"Error:  {response.text}"}, status_code=500)

        # Save image bytes to a temporary file
        temp_image_path = f"temp_{generate_unique_job_id()}.png"
        with open(temp_image_path, "wb") as image_file:
            image_file.write(image_bytes)

        # Return the image file as a response
        return FileResponse(temp_image_path, media_type="image/png", filename="smarts_image.png")

    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error predict_from_pdb_file: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)
    # finally:
    #     if temp_image_path and os.path.exists(temp_image_path):
    #         os.remove(temp_image_path)

@router.post('/from-fasta')
def sequance_to_smiles(
    sequance: str = Form(...),
    current_user: AuthProfile = require_auth()
):
    """Predict SMILES from a sequance"""

    try:
        smiles = fasta_to_peptide_smiles(sequance)
        if smiles:
            log.info("Canonical SMILES:", smiles)
            result = {
                "smiles": smiles
            }
        
            return JSONResponse(content={"status": "success", "data": result}, status_code=200)
        else:
            return JSONResponse(content={"status": "error", "data": "RDKit couldn't parse sequance."}, status_code=500)

    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error predict_from_pdb_file: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)
