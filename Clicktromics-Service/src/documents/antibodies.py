from pydantic import BaseModel, Field
from typing import List

class AntibodyDocument(BaseModel):
    ID: str = Field(..., description="Antibody ID", max_length=100)
    heavy_sequence: str = Field(..., description="Heavy Sequence", max_length=505)
    light_sequence: str = Field(description="Light Sequence")
    disease: str = Field(description="Disease Name")
    targets: List[str] = Field(default_factory=list, description="Targets")