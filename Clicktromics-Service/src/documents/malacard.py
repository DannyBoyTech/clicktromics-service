from typing import List, Optional
from pydantic import BaseModel, Field


class Phenotype(BaseModel):
    phenotype: str = Field(...)
    hpo: Optional[str] = Field(None)
    hpo_freg: Optional[str] = Field(None)


class Gene(BaseModel):
    gene_name: str = Field(...)
    description: Optional[str] = Field(None)
    category: Optional[str] = Field(None)
    score: Optional[str] = Field(None)
    variation: Optional[List[str]] = Field([])


class Drug(BaseModel):
    drug_name: str = Field(...)
    status: str = Field(...)


class Variant(BaseModel):
    gene_name: str = Field(...)
    rsid: str = Field(...)
    clinvar_id: str = Field(...)
    significances: List[str] = Field(...)


class DiseaseDocument(BaseModel):
    main_name: str = Field(...)
    description: Optional[str] = Field(None)
    aliases: Optional[List[str]] = Field([])
    phenotypes: Optional[List[Phenotype]] = Field([])
    genes: Optional[List[Gene]] = Field([])
    drugs: Optional[List[Drug]] = Field([])
    variants: Optional[List[Variant]] = Field([])
