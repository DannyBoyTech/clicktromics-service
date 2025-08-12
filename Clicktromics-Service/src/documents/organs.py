from pydantic import BaseModel, Field
from typing import List

class OrganDocument(BaseModel):
    name: str = Field(..., description="Organ name")
    genes: List[str] = Field(default_factory=list, description="Genes")



