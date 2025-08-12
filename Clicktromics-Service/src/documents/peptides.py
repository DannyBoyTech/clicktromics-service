from pydantic import BaseModel, Field
from typing import List, Optional

class PeptideDocument(BaseModel):
    name: str = Field(..., description="Name of the peptide")
    description: Optional[str] = Field(None, description="Brief description of the peptide")
    sequence: Optional[str] = Field(None, description="Amino acid sequence of the peptide")
    smiles: Optional[str] = Field(None, description="SMILES format of the peptide")
    targets: List[str] = Field(default_factory=list, description="List of targets")
    research_areas: List[str] = Field(default_factory=list, description="Applications or research areas")
    form: Optional[str] = Field(None, description="Form of the peptide (e.g., lyophilized, solution)")
    source: str = Field(..., description="The Source from where we fetch the peptide")

    class Config:
        allow_population_by_field_name = True
