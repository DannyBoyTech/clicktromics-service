from typing import Optional, List
from pydantic import BaseModel, Field

class DiseaseDocument(BaseModel):
    name: str = Field(..., description="Disease Name")
    search_name: Optional[str] = Field(None, description="Disease Name Formated")
    category: Optional[List[str]] = Field([], description="Disease Category")
    Data_score: Optional[float] = Field(None, description="Data_score")