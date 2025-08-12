import requests
from src.logger import Logger

logging = Logger.get_logger()

OPENTARGETS_GRAPHQL_BASE_URL = 'https://api.platform.opentargets.org/api/v4/graphql'

def get_target_compounds(target_id):
    """Get compounds associated with a target from OpenTargets"""
    query = '''
        query GetTargetDrugs($targetId: String!) {
            target(ensemblId: $targetId) {
                knownDrugs {
                    rows {
                        drug {
                            id
                            name
                            drugType
                            description
                            isApproved
                            mechanismsOfAction{  
                            uniqueTargetTypes
                            uniqueActionTypes
                            rows{
                                targetName
                                mechanismOfAction
                                actionType
                            }
                            }
                        }
                    }
                }
            }
        }
    '''
    variables = {'targetId': target_id}
    try:
        response = requests.post(OPENTARGETS_GRAPHQL_BASE_URL, json={'query': query, 'variables': variables})
        response.raise_for_status()
        data = response.json()
        return [drug.get("drug") for drug in data.get('data', {}).get('target', {}).get('knownDrugs', {}).get('rows', [])]
    except Exception as e:
        print(f"Error getting compounds: {e}")
        return []

    
def entity_search(query_string, entityName):
    query = """
        query searchEntities($queryString: String!) {
            search(queryString: $queryString, , entityNames:["{target}"]) {
                total
                hits {
                    id
                    entity
                    name
                    description
                }
            }
        }
    """
    query = query.replace("{target}", entityName)
    variables = {
        "queryString": query_string
    }

    # make request
    res_json = None
    r = requests.post(
        OPENTARGETS_GRAPHQL_BASE_URL,
        headers={'Content-Type': 'application/json'},
        json={'query': query, 'variables': variables}
    )
    try:
        r.raise_for_status()
        res_json: dict = r.json()
    except Exception as e:
        err_res = r.json()
        logging.info(err_res)
        raise e
    
    hits = res_json.get('data', {}).get('search', {}).get('hits', [])
    
    return hits[:10]


def disease_target_search(efoId: str):
    # Define the GraphQL query and variables
    query = """
    query associatedTargets($efoId: String!) {
        disease(efoId: $efoId) {
            id
            name
            description
            associatedTargets {
                count
                rows {
                    target {
                        id
                        approvedSymbol
                        approvedName
                    }
                    score
                }
            }
        }
    }
    """
    variables = {
        "efoId": efoId
    }

    # make request
    res_json = None
    r = requests.post(
        OPENTARGETS_GRAPHQL_BASE_URL,
        headers={'Content-Type': 'application/json'},
        json={'query': query, 'variables': variables}
    )
    try:
        r.raise_for_status()
        res_json: dict = r.json()
    except Exception as e:
        err_res = r.json()
        logging.info(err_res)
        raise e

    disease_target_results = res_json['data']['disease']
    disease_target_results['targets'] = disease_target_results['associatedTargets']['rows'][:10]

    return disease_target_results

def disease_lookup(efoId: str):
    # Define the GraphQL query and variables
    query = """
    query diseaseLookup($efoId: String!) {
        disease(efoId: $efoId) {
            id
            name
            description
            dbXRefs
        }
    }
    """
    variables = {
        "efoId": efoId
    }

    # make request
    res_json = None
    r = requests.post(
        OPENTARGETS_GRAPHQL_BASE_URL,
        headers={'Content-Type': 'application/json'},
        json={'query': query, 'variables': variables}
    )
    try:
        res_json: dict = r.json()
        r.raise_for_status()
    except Exception as e:
        logging.info(res_json)
        raise e

    disease_results = res_json['data']['disease']

    return disease_results


def target_lookup(ensemblId: str):
    # Define the GraphQL query and variables
    query = """
    query targetLookup($ensemblId: String!) {
        target(ensemblId: $ensemblId) {
            id
            approvedSymbol
            approvedName
            functionDescriptions
            proteinIds {
                id
                source
            }
            
        }
    }
    """
    variables = {
        "ensemblId": ensemblId
    }

    # make request
    res_json = None
    r = requests.post(
        OPENTARGETS_GRAPHQL_BASE_URL,
        headers={'Content-Type': 'application/json'},
        json={'query': query, 'variables': variables}
    )
    try:
        res_json: dict = r.json()
        r.raise_for_status()
    except Exception as e:
        logging.info(res_json)
        raise e

    target_results = res_json['data']['target']

    return target_results
