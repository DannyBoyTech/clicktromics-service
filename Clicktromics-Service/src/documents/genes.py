from pydantic import BaseModel, Field
from typing import List

class GeneDocument(BaseModel):
    geneName: str = Field(..., description="Target")
    aliases: List[str] = Field(default_factory=list, description="Target aliases")
    id: str = Field(..., description="Target Id")

