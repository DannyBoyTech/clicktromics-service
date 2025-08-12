from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class MondoRelation(BaseModel):
    has_phenotype: Optional[List[str]] = Field(default_factory=list, description="List of HPO IDs representing phenotypes")
    other: Optional[Dict[str, List[str]]] = Field(default_factory=dict, description="Other relations mapped as {relation_type: [term_ids]}")

class MondoTermDocument(BaseModel):
    id: str = Field(..., alias="_id", description="MONDO ID of the disease")
    name: Optional[str] = Field(None, description="Name of the MONDO term")
    definition: Optional[str] = Field(None, description="Definition of the MONDO term")
    synonyms: Optional[List[str]] = Field(default_factory=list, description="List of synonyms")
    xrefs: Optional[List[str]] = Field(default_factory=list, description="External references (cross-references)")
    relations: Optional[MondoRelation] = Field(default_factory=MondoRelation, description="Relations to other ontological terms")

    class Config:
        allow_population_by_field_name = True

class HPORelation(BaseModel):
    is_a: Optional[List[str]] = Field(default_factory=list, description="HPO terms this term is a subclass of")
    part_of: Optional[List[str]] = Field(default_factory=list, description="HPO terms this term is a part of")

class HPOTermDocument(BaseModel):
    id: str = Field(..., alias="_id", description="HPO ID of the term")
    name: Optional[str] = Field(None, description="Name of the HPO term")
    definition: Optional[str] = Field(None, description="Definition of the HPO term")
    synonyms: Optional[Dict] = Field(default_factory=list, description="List of synonyms")
    relations: Optional[HPORelation] = Field(default_factory=HPORelation, description="Ontology relations for the term")

    # populate fields using their Python attribute names
    class Config:
        allow_population_by_field_name = True


class HPOAnnotationDocument(BaseModel):
    database_id: str = Field(..., description="MONDO ID of the disease")
    disease_name: Optional[str] = Field(None, description="Name of the disease")
    hpo_id: str = Field(..., description="HPO ID associated with the disease")
    evidence: Optional[str] = Field(None, description="Type of evidence (e.g., IEA, PCS, TAS, etc.)")
    frequency: Optional[str] = Field(None, description="Frequency of the annotation")


class Node(BaseModel):
    id: str = Field(..., description="Node identifier (e.g., MONDO, Gene, UniProt)")
    name: Optional[str] = Field(None, description="Human-readable name of the node")
    type: Optional[str] = Field(None, description="Semantic category (e.g., gene, disease, drug)")
    source: Optional[str] = Field(None, description="Source of the info")

class KGEdgeDocument(BaseModel):
    source: Optional[Node] = Field(None, description="Source node of the edge")
    target: Optional[Node] = Field(None, description="Target node of the edge")
    relation: Optional[str]  = Field(None, description="Relation type")
    publications: Optional[List[str]] = Field(default_factory=list, description="List of PubMed or external references")
    evidence: Optional[str] = Field(None, description="Evidence supporting the edge (text)")

# KGEdgeDocument.relation
# {
#     'anatomy_anatomy',
#     'anatomy_protein_absent',
#     'anatomy_protein_present',
#     'bioprocess_bioprocess',
#     'bioprocess_protein',
#     'cellcomp_cellcomp',
#     'cellcomp_protein',
#     'contraindication',
#     'disease_disease',
#     'disease_phenotype_negative',
#     'disease_phenotype_positive',
#     'disease_protein',
#     'drug_drug',
#     'drug_effect',
#     'drug_protein',
#     'exposure_bioprocess',
#     'exposure_cellcomp',
#     'exposure_disease',
#     'exposure_exposure',
#     'exposure_molfunc',
#     'exposure_protein',
#     'indication',
#     'molfunc_molfunc',
#     'molfunc_protein',
#     'off-label use',
#     'pathway_pathway',
#     'pathway_protein',
#     'phenotype_phenotype',
#     'phenotype_protein',
#     'protein_protein'
# }
