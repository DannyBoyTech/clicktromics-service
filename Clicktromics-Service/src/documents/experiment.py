from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, timezone
from enum import Enum
from src.utils import generate_unique_job_id
from src.documents.antibodies import AntibodyDocument
from src.documents.jobs import JobDocument

class TargetTypeEnum(str, Enum):
    SEQUENCE = "Sequence"
    PDB = "PDB"
    SUGGEST = "suggest/search"

class TargetType(BaseModel):
    name: TargetTypeEnum = Field(..., description="Target type")
    class Config:
        arbitrary_types_allowed = True


class DrugDocument(BaseModel):
    drugbank_id: str = Field(default_factory=lambda: generate_unique_job_id(), description="DrugBank ID")  # required
    drug_name: Optional[str] = Field(None, description="Drug name")
    simple_description: Optional[str] = Field(None, description="Short description of the drug")
    chem_smiles: Optional[str] = Field(None, description="Chemical SMILES notation")
    sequence_smiles: Optional[str] = Field(None, description="Sequence SMILES, if available")
    drug_synonyms: Optional[str] = Field(None, description="Synonyms for the drug")
    groups: Optional[List[str]] = Field([], description="Drug approval groups")
    half_life: Optional[str] = Field(None, alias="half-life", description="Half-life details")
    description: Optional[str] = Field(None, description="Drug indication")
    mechanism_of_action: Optional[str] = Field(None, description="Pharmacodynamics")
    JCHEM_TRADITIONAL_IUPAC: Optional[str] = Field(None, description="Traditional IUPAC name")
    GENERIC_NAME: Optional[str] = Field(None, description="Generic name")
    Lipinski: Optional[float] = Field(None, description="Lipinski rule score")
    Lipinski_drugbank_approved_percentile: Optional[float] = Field(None, description="Percentile among DrugBank approved drugs")
    QED: Optional[float] = Field(None, description="Quantitative Estimation of Drug-likeness")
    hydrogen_bond_acceptors: Optional[float] = Field(None, description="Number of hydrogen bond acceptors")
    hydrogen_bond_donors: Optional[float] = Field(None, description="Number of hydrogen bond donors")
    logP: Optional[float] = Field(None, description="LogP value")
    molecular_weight: Optional[float] = Field(None, description="Molecular weight")
    organs: Optional[List[str]] = Field([], description="Organs associated with the drug")

    class Config:
        arbitrary_types_allowed = True


class Payload(BaseModel):
    spacc: Optional[str] = Field(None, description="SPACC info")
    linker: Optional[str] = Field(None, description="Linker molecule smiles")
    glycan: Optional[dict] = Field(None, description="glycan molecule info")
    glycanLinker: Optional[dict] = Field(None, description="glycanLinker molecule info")
    linkerName: Optional[str] = Field(None, description="Linker molecule info")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    @field_serializer("created_at")
    def serialize_created_at(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format for created_at
    
    @field_serializer("updated_at")
    def serialize_updated_at(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format for updated_at

class ExperimentDocument(BaseModel):
    title: Optional[str] = Field(None, description="Experiment title", max_length=100)
    description: Optional[str] = Field(None, description="Experiment description", max_length=505)
    organ: Optional[str] = Field(None, description="Experiment targeted organ", max_length=100)
    disease: Optional[str] = Field(None, description="Experiment disease", max_length=100)
    stage: Optional[JobDocument] = Field(None, description="the current Job status")
    experiment_id: str = Field(default_factory=lambda: generate_unique_job_id(), description="Experiment identifier")
    drug: Optional[DrugDocument] = Field(None, description="Linked drug")
    payload: Optional[Payload] = Field(None, description="Linked payload")
    antibody: Optional[AntibodyDocument] = Field(None, description="Linked antibody")
    jobs: Optional[List[JobDocument]] = Field(default_factory=list, description="List of sub-jobs")
    user_email: str = Field(..., description="Email of the user who owns the experiment")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    files: Optional[Dict] = Field({"rsid": "", "diffab_input":"", "uploads":[], "homelette":"", "musite":"", "boltz": "", "diffab_pdb": "", "peptide": "", "gnina": []}, description="Experiment Files")

    class Config:
        arbitrary_types_allowed = True

    @field_serializer("created_at")
    def serialize_created_at(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format for created_at
    
    @field_serializer("updated_at")
    def serialize_updated_at(self, timestamp: datetime, _info):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")  # Custom format for updated_at