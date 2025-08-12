from src.logger import Logger
import requests

logging = Logger.get_logger()

UNIPROT_REST_API_KB_BASE_URL = 'https://rest.uniprot.org/uniprotkb'


def search_for_gene(query: str):
    params = {
            'query':  f"(gene_exact:{query})",
            'format': 'json'
    }
    try:
        response = requests.get(UNIPROT_REST_API_KB_BASE_URL + "/search", params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
    except Exception as e:
        logging.info(str(e))
        raise e

    full_name_value = ""

    for result in results:
        description = result.get('proteinDescription', {})
        recommended_name = description.get('recommendedName')
        if not recommended_name:
            recommended_name = description.get('submissionNames', [])
            full_name = recommended_name[0].get('fullName', {})
            full_name_value = full_name.get('value', "")
        else:
            full_name = recommended_name.get('fullName', {})
            full_name_value = full_name.get('value', "")

        if full_name_value == query:
            return result["primaryAccession"]
        
    return None

def get_compound_by_id(uniprot_id: str):
    # make request
    res_json = None
    r = requests.post(f'{UNIPROT_REST_API_KB_BASE_URL}/{uniprot_id}',
        headers={'Accept': 'application/json'},
        data=uniprot_id
    )
    try:
        res_json = r.json()
        r.raise_for_status()
    except Exception as e:
        logging.info(res_json)
        raise e

    sequence = None
    tissue_organ_system = []
    condition_disease = []
    full_name_value = ""
    genes_names = []
    if 'sequence' in res_json and 'value' in res_json['sequence']:
        # Retrieve the sequence res_json if available.
        sequence = {
                "value": res_json["sequence"].get("value") if "value" in res_json["sequence"] else None,
                "length": res_json["sequence"].get("length") if "length" in res_json["sequence"] else None,
                "molWeight": res_json["sequence"].get("molWeight") if "molWeight" in res_json["sequence"] else None
        }
        if "comments" in res_json:
            for comment in res_json["comments"]:
                if comment.get("commentType") == "TISSUE SPECIFICITY":
                    tissue_organ_system.extend(
                        [text.get("value") for text in comment.get("texts", []) if "value" in text]
                    )
                if comment.get("commentType") == "DISEASE":
                    if "disease" in comment:
                        condition_disease.append({
                            "diseaseId": comment["disease"].get("diseaseId") if "diseaseId" in comment["disease"] else None,
                            "acronym": comment["disease"].get("acronym") if "acronym" in comment["disease"] else None,
                            "description": comment["disease"].get("description") if "description" in comment["disease"] else None
                        })
        if "genes" in res_json:
            for gene in res_json["genes"]:
                gene_names = gene.get("geneName", {}).get("value", "")
                for synonym in gene.get("synonym", {}):
                    if isinstance(synonym, dict):
                        gene_names += synonym.get("value", "")
                    else:
                        gene_names += synonym
                genes_names.append(gene_names)   

        description = res_json.get('proteinDescription', {})
        recommended_name = description.get('recommendedName')
        if not recommended_name:
            recommended_name = description.get('submissionNames', [])
            full_name = recommended_name[0].get('fullName', {})
            full_name_value = full_name.get('value', "")
        else:
            full_name = recommended_name.get('fullName', {})
            full_name_value = full_name.get('value', "")

    # Scores range typically from 1 to 5 stars, with:
        # 5 stars: Highly curated, comprehensive entry with extensive experimental evidence.
        # 1 star: Minimal annotation, mostly predicted or inferred data.
    return {
        "name" : full_name_value,
        "genes": genes_names,
        "organs/systems": tissue_organ_system,
        "condition/disease": condition_disease,
        "sequence": sequence,
        'annotationScore': res_json["annotationScore"],
        'organism': {
            "scientificName": res_json["organism"].get("scientificName", ""),
            "commonName": res_json["organism"].get("commonName", "")
        }
    }