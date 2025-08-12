from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class RsidDocument(BaseModel):
    rsid: str = Field(..., description="SNP identifier, e.g., rs1342343954")
    chr: Optional[str] = Field(None, description="Chromosome")
    ref: Optional[str] = Field(None, description="Reference allele")
    alt: Optional[str] = Field(None, description="Alternate allele")
    system: Optional[str] = Field(None, description="Organ system affected")
    genes: Optional[List[str]] = Field(None, description="List of mapped genes")
    aliases: Optional[Dict[str, List[str]]] = Field(None, description="Gene aliases mapping")
    drugs: Optional[List[Dict]] = Field(default_factory=list, description="Associated drugs")
    disease: Optional[str] = Field(None, description="Associated disease")
    strongest_snp_risk_allele: Optional[str] = Field(None, description="Risk allele")
    risk_allele_frequency: Optional[str] = Field(None, description="Risk allele frequency")
    p_value: Optional[float] = Field(None, description="P-value from association")
    drugs: Optional[str] = Field(None, description="Associated drugs")

    class Config:
        schema_extra = {
            "example": {
                "disease": "Myeloperoxidase deficiency",
                "chr": "17",
                "ref": "C",
                "alt": "T",
                "system": "Endocrine",
                "rsid": "rs774984207",
                "genes": [
                "MPO"
                ],
                "aliases": {
                "MPO": [
                    "-"
                ]
                },
                "risk_allele_frequency": None,
                "p_value": None,
                "drugs": "Paroxetine,Metoclopramide,Dapsone,Tryptamine,Hydralazine,Mefenamic acid,Aminoquinuride"
            },
        }