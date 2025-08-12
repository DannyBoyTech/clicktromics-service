from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from src.utils import generate_unique_job_id

class Disease(BaseModel):
    diseaseId: Optional[str] = None
    acronym: Optional[str] = None
    description: Optional[str] = None

class Polypeptide(BaseModel):
    name: Optional[str] = None
    uniprot_id: Optional[str] = None
    pdb_rcsb_ids: Optional[str] = None

class Organism(BaseModel):
    scientificName: Optional[str] = None
    commonName: Optional[str] = None

class Sequence(BaseModel):
    value: Optional[str] = None
    length: Optional[int] = None
    molWeight: Optional[float] = None

class Target(BaseModel):
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    polypeptide: Optional[Polypeptide] = None
    TISSUE_SPECIFICITY: Optional[List[str]] = Field(default_factory=list)
    disease: Optional[List[Disease]] = Field(default_factory=list)
    annotationScore: Optional[float] = None
    organism: Optional[Organism] = None
    genes: Optional[Dict[str, List[str]]] = Field(default_factory=dict)
    gene_names: Optional[List[str]] = Field(default_factory=list)
    sequence: Optional[Sequence] = None
    description: Optional[str] =  Field(None, description="Target description")

    class Config:
        extra = "ignore"

class DrugDocument(BaseModel):
    drugbank_id: str = Field(default_factory=lambda: generate_unique_job_id(), description="DrugBank ID")  # required
    drug_name: Optional[str] = Field(None, description="Drug name")
    simple_description: Optional[str] = Field(None, description="Short description of the drug")
    chem_smiles: Optional[str] = Field(None, description="Chemical SMILES notation")
    sequence_smiles: Optional[str] = Field(None, description="Sequence SMILES, if available")
    drug_synonyms: Optional[str] = Field(None, description="Synonyms for the drug")
    # targets: Optional[List[Target]] = Field([], description="Targets information")
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

    class Config:
        extra = "ignore"
