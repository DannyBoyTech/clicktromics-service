from pydantic import BaseModel
from src.config import DEFAULT_SEQUENCE, DEFAULT_SMILES
from typing import Optional, Generic, TypeVar, List
from fastapi import Query
from pydantic.generics import GenericModel

T = TypeVar("T")

class PdbRequest(BaseModel):
    pdb_id: Optional[str] = None

class DockingJobRequest(BaseModel):
    musite_res_number: int = Query(default=2, ge=0, description="Musite residue number, should be bigger than 0 and not more than the number of residues in the musite file")
    musite_file: Optional[str] = None
    pdb_file: str
    spacc: str

class PeptideJobRequest(BaseModel):    
    peptide_protein_sequence: str = DEFAULT_SEQUENCE
    peptide_length: int = 15

class BoltzJobRequest(BaseModel):
    boltz_sequence : str = DEFAULT_SEQUENCE

class HomeletteUseRequest(BaseModel):
    antibody_id: str

class ClickRequest(BaseModel):
    drugbankId: Optional[str] = None
    smiles: Optional[str] = None
    isPDC: bool = False

class ClickADCRequest(BaseModel):
    drugbankId: Optional[str] = None
    smiles: Optional[str] = None

class ClickPDCRequest(BaseModel):
    drugbankId: Optional[str] = None
    target_peptide_smiles: Optional[str] = None
    peptide_smiles: str
    linker_target_peptide_smiles: str = r"O=C(CCC(NCCSSCCC(O(*))=O)=O)N1C(C=CC=C2)=C2C#CC(C=CC=C3)=C3C1"

class UploadSmileRequest(BaseModel):
    job_id: str
    smiles: str = DEFAULT_SMILES

class AdmetPredictRequest(BaseModel):
    smiles: str = "O(c1ccc(cc1)CCOC)CC(O)CNC(C)C"

class SmilesRequest(BaseModel):
    smiles: str = "O(c1ccc(cc1)CCOC)CC(O)CNC(C)C"

class ChatMessage(BaseModel):
    query: str
    conversation_id: str

## Search ##

class SearchOrganRequest(BaseModel):
    name: str = Query(..., description="Organ name")
    page: int = Query(default=1, ge=1, description="Page number")
    page_size: int = Query(default=10, ge=1, le=100, description="Number of genes per page"),

class SearchGeneRequest(BaseModel):
    name: str = Query(..., description="Gene name")
 
class SearchDrugRequest(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None

class SearchAntibodyRequest(BaseModel):
    input: str = Query("her2" , description="Input")
    category: str = Query("target", description="Category")
    page: int = Query(default=1, ge=1, description="Page number")
    page_size: int = Query(default=10, ge=1, le=100, description="Number of antibodies per page")

class SearchDiseaseRequest(BaseModel):
    name: str = Query(..., description="Disease name")

class PaginatedResponse(GenericModel, Generic[T]):
    total: int
    page: int
    page_size: int
    results: List[T]

## Job Response Models ##

class JobData(BaseModel):
    job_id: str
    message: str

class JobSuccessResponse(BaseModel):
    status: str = "success"
    data: JobData

class JobErrorResponse(BaseModel):
    status: str = "error"
    message: str
##  ##