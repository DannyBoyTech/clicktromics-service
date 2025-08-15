from src.logger import Logger
from fastapi import APIRouter , Depends, Query
from fastapi.responses import JSONResponse
from src.repo.organs import OrganRepo
from src.repo.genes import GeneRepo
from src.repo.drugs import DrugRepo
from src.repo.antibodies import AntibodyRepo
from src.repo.kg import KgEdgeRepo
from src.repo.mondo import MondoRepo
from src.repo.disease import DiseaseRepo
from src.repo.malacard import MalacardRepo
from src.repo.hpo import HpoAnnotationRepo, HpoRepo
from src.repo.peptides import PeptideDocument, PeptideRepo 
from src.helper.opentargets import opentargets
from src.helper.uniprot import uniprot
from src.utils import get_homelette_Object
from src.config import DEFAULT_BUCKET_NAME, USE_AWS, LOCAL_STORAGE_PATH
from src.helper.aws.s3 import get_s3_service, S3Service
from src.request_model import SearchOrganRequest, SearchDiseaseRequest, SearchGeneRequest, SearchAntibodyRequest
from rapidfuzz import process, fuzz
from src.helper.scrape import AdvancedScraper
from src.auth.dependencies import require_auth
from src.documents.profile import AuthProfile
import asyncio
import os

log = Logger.get_logger()
router = APIRouter(prefix="/search", tags=["Search"])

@router.post("/antibody")
async def search_antibody(
    request_body: SearchAntibodyRequest,
    repo: AntibodyRepo = Depends(lambda: AntibodyRepo()),
    s3: S3Service = Depends(get_s3_service),
    current_user: AuthProfile = require_auth()
):
    """Search for antibody in our database"""
    if not request_body.input:
        log.info(f"input_ is empty, please provide valid input")
        return JSONResponse(content={"status": "error", "message": "input_ is empty, please provide valid input"}, status_code=400)
    
    if not request_body.category:
        log.info(f"category is empty, please provide valid category")
        return JSONResponse(content={"status": "error", "message": "category is empty, please provide valid category"}, status_code=400)
    
    try:
        if request_body.category == "target":
            antbodies = await repo.find_by_target(request_body.input, request_body.page, request_body.page_size)
        else:
            antbodies = await repo.find(request_body.input, request_body.page, request_body.page_size)

    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error search_drug: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)


    if antbodies.total == 0:
        return JSONResponse(status_code=404, content={"status": "error", "message":"Not found in database"})
    
    try:
        res = []
        for antibody in antbodies.results:
            if (USE_AWS and s3.check_object_existence(DEFAULT_BUCKET_NAME, get_homelette_Object(antibody.ID))) or os.path.exists(os.path.join(LOCAL_STORAGE_PATH, get_homelette_Object(antibody.ID))):
                antibody_data = {
                    **antibody.model_dump(),
                    "pdb_file": get_homelette_Object(antibody.ID)
                }
                antibody_data.pop("targets", None)
                res.append(antibody_data)

        if len(res) == 0:
            log.error(f"Homelette file not found for: {antbodies}")
            return JSONResponse(status_code=404, content={"status": "error", "message":"Not found in database"})

        log.info(f"Search completed, pdb_homelette_id: {res}")

        antbodies.results = res
        return JSONResponse(content={"status": "success", "data": antbodies.dict()}, status_code=200)
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error occurred"
        log.error(f"Error search_antibody: {error_message}")
        return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

@router.get("/diseases/category")
async def search_diseases_by_category(
    name: str = Query(..., description="Disease categories name"),
    repo: DiseaseRepo = Depends(lambda: DiseaseRepo()),
    current_user: AuthProfile = require_auth()
):
    try:
        if name is None or name == "":
            return JSONResponse(status_code=400, content={"status": "error", "message":"name is empty"})
        
        matches = await repo.find_category_by_query_list(name.lower())

        return JSONResponse(content={"status": "success", "data": {
           "query": name,
           "matches": [doc.model_dump() for doc in matches]
        }}, status_code=200)
    
    except Exception as e:
        error_message = str(e) or "Unknown error occurred"
        log.error(f"Error in search_disease: {error_message}")
        return JSONResponse(
            content={"status": "error", "message": f"Error encountered during processing: {error_message}"},
            status_code=500,
        )

@router.post("/disease/{name}/drugs")
async def search_drugs_by_disease(
    name: str,
    repo: MalacardRepo = Depends(lambda: MalacardRepo()),
    drug_repo: DrugRepo = Depends(lambda: DrugRepo()),
    current_user: AuthProfile = require_auth()
):
    try:
        if name is None or name == "":
            return JSONResponse(status_code=400, content={"status": "error", "message":"name is empty"})
        
        doc = await repo.find_disease_by_name(name)
    
        if not doc:
            return JSONResponse(status_code=404, content={"status": "error", "message":f"{name} Not Found"})
        
        nutraceutical = []
        drugs = []
        for drug in  doc.drugs:
            if "Nutraceutical" in drug.status:
                nutraceutical.append(drug.drug_name)
            else:
                drug_info = await drug_repo.find_by_name(drug.drug_name)
                if drug_info:
                    drugs.append(drug_info.model_dump())

        log.info(len(drugs))
        return JSONResponse(content={"status": "success", "data":{
            'nutraceutical': nutraceutical,
            'drugs': drugs
        }}, status_code=200)
    
    except Exception as e:
        error_message = str(e) or "Unknown error occurred"
        log.error(f"Error in search_disease: {error_message}")
        return JSONResponse(
            content={"status": "error", "message": f"Error encountered during processing: {error_message}"},
            status_code=500,
        )
    
@router.post("/disease/{name}/genes")
async def search_genes_by_disease(
    name: str,
    repo: MalacardRepo = Depends(lambda: MalacardRepo()),
    antibody_repo: AntibodyRepo = Depends(lambda: AntibodyRepo()),
    current_user: AuthProfile = require_auth()
):
    try:
        if name is None or name == "":
            return JSONResponse(status_code=400, content={"status": "error", "message":"name is empty"})
        
        doc = await repo.find_disease_by_name(name)
    
        if not doc:
            return JSONResponse(status_code=404, content={"status": "error", "message":f"{name} Not Found"})
        
        genes = []
        for gene in  doc.genes:
            exists = await antibody_repo.count_by_target(gene.gene_name)
            if exists:
                genes.append(gene.model_dump())

        return JSONResponse(content={"status": "success", "data": genes}, status_code=200)
    
    except Exception as e:
        error_message = str(e) or "Unknown error occurred"
        log.error(f"Error in search_disease: {error_message}")
        return JSONResponse(
            content={"status": "error", "message": f"Error encountered during processing: {error_message}"},
            status_code=500,
        )

# @router.post("/disease")
# async def search_disease(
#     request: SearchDiseaseRequest,
#     repo: MondoRepo = Depends(lambda: MondoRepo())
# ):
#     try:
#         if request.name is None or request.name == "":
#             return JSONResponse(status_code=400, content={"status": "error", "message":"name is empty"})
        
#         norm_disease = repo.normalize(request.name)
#         candidates = await repo.search_by_name_fragment(norm_disease)


#         if not candidates :
#             return JSONResponse(
#                 status_code=404,
#                 content={"status": "error", "message": "Disease not found"}
#             )
        
#         matches = []
#         name_map = {term.name: term for term in candidates if term.name}
#         mondo_keys = list(name_map.keys())

#         if norm_disease in name_map:
#             matched = name_map[norm_disease].model_dump()
#             matches.append({**matched, "score": 100})

#         # Fuzzy match
#         match = process.extract(norm_disease, mondo_keys, scorer=fuzz.token_sort_ratio)
#         for best, score, _ in match:
#             if score > 70 and not best == norm_disease:
#                 matches.append({ **name_map[best].model_dump(), "score": score})
            

#         return JSONResponse(content={"status": "success", "data": {
#            "query": request.name,
#            "matches": matches
#         }}, status_code=200)
    
#     except Exception as e:
#         error_message = str(e) if str(e) else "Unknown error occurred"
#         log.error(f"Error search_disease: {error_message}")
#         return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

# @router.get("/diseases/{mondo_id}/info")
# async def get_info_for_disease(
#     mondo_id: str,
#     repo: KgEdgeRepo = Depends(lambda: KgEdgeRepo()),
#     hpo_ann_repo: HpoAnnotationRepo = Depends(lambda: HpoAnnotationRepo()),
#     hpo_term_repo: HpoRepo = Depends(lambda: HpoRepo())
# ):
#     try: 

#         if mondo_id.count("_") > 0:
#             mondo_id = mondo_id.replace("_", ":")

#         hp = await hpo_ann_repo.search_by_disease_id(
#             mondo_id,
#             1,
#             100
#         )

#         hpo = await hpo_term_repo.find_by_ids([doc.hpo_id for doc in hp.results ])

#         if mondo_id.count(":") > 0:
#             mondo_id = int(mondo_id.split(":")[1])
#         elif mondo_id.count("_") > 0:
#             mondo_id = int(mondo_id.split("_")[1])

#         phenotype_protein = await repo.find_by_relation_multi_source(
#             [hpos.id.split(":")[1].lstrip("0") for hpos in hpo],
#             "phenotype",
#             "phenotype",
#             "phenotype_protein"
#         )

#         disease_phenotype_negative = await repo.find_by_relation(
#             mondo_id,
#             "disease",
#             "phenotype",
#             "disease_phenotype_negative"
#         )

#         disease_phenotype_positive = await repo.find_by_relation(
#             mondo_id,
#             "disease",
#             "phenotype",
#             "disease_phenotype_positive"
#         )

#         nodes = await repo.find_edges_by_node_id(
#             mondo_id
#         )

#         return JSONResponse(content={"status": "success", "data": {
#             "data": [hp.model_dump() for hp in hpo ],
#             "disease_phenotype_negative": disease_phenotype_negative,
#             "disease_phenotype_positive": disease_phenotype_positive,
#             "phenotype_protein": phenotype_protein,
#             "nodes": [node.model_dump() for node in nodes.results]
#         }}, status_code=200)
    
#     except Exception as e:
#         error_message = str(e) if str(e) else "Unknown error occurred"
#         log.error(f"Error search_disease: {error_message}")
#         return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

# @router.get("/diseases/{mondo_id}/compounds")
# async def get_compounds_for_disease(
#     mondo_id: str,
#     repo: KgEdgeRepo = Depends(lambda: KgEdgeRepo())
# ):
#     try: 
#         if mondo_id.count(":") > 0:
#             mondo_id = int(mondo_id.split(":")[1])
#         elif mondo_id.count("_") > 0:
#             mondo_id = int(mondo_id.split("_")[1])

#         drugs_by_mondo = await repo.find_by_relation(
#             mondo_id,
#             "disease",
#             "drug",
#             "indication"
#         )
#         proteins_by_mondo = await repo.find_by_relation(
#             mondo_id,
#             "disease",
#             "gene/protein",
#             "disease_protein"
#         )

#         if not len(drugs_by_mondo) and not len(proteins_by_mondo):
#             return JSONResponse(
#                     status_code=404,
#                     content={"status": "error", "message": "No compounds associations found for this MONDO ID"}
#                 )
        
#         drug_ids = [edge.target.id for edge in drugs_by_mondo]
#         proteins_by_drugs = await repo.find_by_relation_multi_source(
#             drug_ids,
#             "drug",
#             "gene/protein",
#             "drug_protein"
#         )

#         drugs = await repo.rank_drug_by_targets(drug_ids)

#         proteins = [
#             {
#                 "id": protein.target.id,
#                 "name": protein.target.name,
#                 "evidence": protein.evidence,
#                 "publications": protein.publications
#             }
#         for protein in  (proteins_by_mondo + proteins_by_drugs)
#         ]

#         return JSONResponse(content={"status": "success", "data": {
#             "data": {
#                 "proteins" : proteins,
#                 "drugs" : [drug.model_dump() for drug in drugs]
#             }
#         }}, status_code=200)
    
#     except Exception as e:
#         error_message = str(e) if str(e) else "Unknown error occurred"
#         log.error(f"Error search_disease: {error_message}")
#         return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

# @router.post("/organ")
# async def search_organ(
#     request: SearchOrganRequest,
#     repo: OrganRepo = Depends(lambda: OrganRepo())
# ):
#     try:
#         if request.name is None or request.name == "":
#             return JSONResponse(status_code=400, content={"status": "error", "message":"Please select a valid organ"})
        
#         name = request.name.replace(" ", "_").lower()
#         result = await repo.find_by_name(name, request.page, request.page_size)

#         if result.total == 0:
#             return JSONResponse(
#                 status_code=404,
#                 content={"status": "error", "message": "Organ not found"}
#             )

#         log.info("Successfully fetched organs data from memory")
#         return JSONResponse(content={"status": "success", "data": result.dict()}, status_code=200)
    
#     except Exception as e:
#         error_message = str(e) if str(e) else "Unknown error occurred"
#         log.error(f"Error search_organ: {error_message}")
#         return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

# @router.post("/gene")
# async def search_gene(
#     request: SearchGeneRequest,
#     repo: GeneRepo = Depends(lambda: GeneRepo()),
#     drugRepo: DrugRepo = Depends(lambda: DrugRepo())
# ):
#     try:
#         if request.name is None or request.name == "":
#             return JSONResponse(status_code=400, content={"status": "error", "message":"name is empty"})
        
#         name = request.name.strip().upper()
#         result = await repo.find_by_name(name)

#         if not result:
#             result = await repo.find_by_aliases(name)
#             if not result:
#                 return JSONResponse(
#                     status_code=404,
#                     content={"status": "error", "message": "Gene not found"}
#                 )

#         if not result.id:
#             res = opentargets.entity_search(result.geneName, "target")
#             if len(res) > 0:
#                 if res[0]["name"] == result.geneName:
#                     result.id = res[0]['id']

#         opentargets_drug_data = []
#         opentargets_data = {}
#         if result.id:
#             opentargets_data = opentargets.target_lookup(result.id)
#             opentargets_drug_data = opentargets.get_target_compounds(result.id)
#             for drug in opentargets_drug_data:
#                 if drug.get("name"):
#                     drug_doc = await drugRepo.find_by_name(drug["name"].lower())
#                     if drug_doc:
#                         drug["SMILES"] = drug_doc.chem_smiles if drug_doc.chem_smiles else drug_doc.sequence_smiles
#                         drug["logP"] = drug_doc.logP
#                         drug["molecular_weight"] = drug_doc.molecular_weight
#                         drug["Lipinski"] = drug_doc.Lipinski
#                         drug["hydrogen_bond_acceptors"] = drug_doc.hydrogen_bond_acceptors


#             for i, proteinId in enumerate(opentargets_data.get("proteinIds", [])):
#                 if proteinId["source"].split("_")[0] == "uniprot":
#                     uniprot_data = uniprot.get_compound_by_id(proteinId["id"])
#                     opentargets_data["proteinIds"][i] = {
#                         **proteinId,
#                         **uniprot_data
#                     }
#             opentargets_data["proteinIds"] = sorted(opentargets_data["proteinIds"], key=lambda x: x.get("annotationScore", 0), reverse=True)


#         return JSONResponse(content={"status": "success", "data": {
#                 **result.model_dump(),
#                 **opentargets_data,
#                 "drugs": opentargets_drug_data
#         }}, status_code=200)

#     except Exception as e:
#         error_message = str(e) if str(e) else "Unknown error occurred"
#         log.error(f"Error search_organ: {error_message}")
#         return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

# @router.get("/gene/{gene}/compounds")
# async def get_compounds_by_gene(
#     gene: str,
#     scraper: AdvancedScraper = Depends(AdvancedScraper),
#     repo: PeptideRepo = Depends(lambda: PeptideRepo()),
#     gene_repo: GeneRepo = Depends(lambda: GeneRepo()),
# ):
#     try:
#         if gene is None or gene == "":
#             return JSONResponse(status_code=400, content={"status": "error", "message":"name is empty"})
        
#         name = gene.strip().upper()
#         result = await gene_repo.find_by_name(name)

#         if not result:
#             result = await gene_repo.find_by_aliases(name)
#             if not result:
#                 return JSONResponse(
#                     status_code=404,
#                     content={"status": "error", "message": "Gene not found"}
#                 )
            
#         name = result.geneName
#         peptides_doc = await repo.find_by_targets(name)

#         if len(peptides_doc) == 0:
#             peptides_doc = []
#             abcam_results, medchem_results = await asyncio.gather(
#                 scraper.fetch_from_abcam(name),
#                 scraper.fetch_from_medchem(name)
#             )
#             peptides = abcam_results + medchem_results

#             if peptides:
#                 for peptide in peptides:
#                     if peptide.get("sequence", None):
#                         log.info(f"Adding {peptide}")
#                         doc = PeptideDocument(
#                                 name=           peptide.get("name"),
#                                 research_areas= peptide.get("applications", peptide.get("research_areas", "")),
#                                 targets=        list(set(peptide.get("targets",[]) + [name])),
#                                 form=           peptide.get("form", ""),
#                                 sequence=       peptide.get("sequence"),
#                                 description=    peptide.get("description", peptide.get("brief", "")),
#                                 source=         peptide.get("source")
#                         )
#                         peptides_doc.append(doc)
#                         await repo.save(doc)
#                     else:
#                         log.warning(f"Could not add {peptide}")

#         return JSONResponse(content={"status": "success", "data": [peptide.model_dump() for peptide in peptides_doc]}, status_code=200)

#     except Exception as e:
#         error_message = str(e) if str(e) else "Unknown error occurred"
#         log.error(f"Error search_compounds_by_gene: {error_message}")
#         return JSONResponse(content={"status": "error", "message": "Error encountered during processing. Please review the application log for detailed information"}, status_code=500)

    