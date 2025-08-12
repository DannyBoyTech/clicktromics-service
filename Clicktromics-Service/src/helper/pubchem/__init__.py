import requests, json

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def get_pubchem_info(compound_name):
    """Retrieve compound data from PubChem"""
    try:
        # Get CID
        cid_response = requests.get(f"{PUBCHEM_BASE}/compound/name/{compound_name}/cids/JSON")
        cid_response.raise_for_status()
        cid = cid_response.json()['IdentifierList']['CID'][0]
        
        # Get properties
        props_response = requests.get(
            f"{PUBCHEM_BASE}/compound/cid/{cid}/property/Log P,CanonicalSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON"
        )
        props_response.raise_for_status()
        props = props_response.json()['PropertyTable']['Properties'][0]
        
        return {
            'cid': cid,
            'smiles': props.get('CanonicalSMILES', ''),
            'inchikey': props.get('InChIKey', ''),
            'formula': props.get('MolecularFormula', ''),
            'weight': props.get('MolecularWeight', '')
        }
    except Exception as e:
        print(f"Error fetching PubChem data for {compound_name}: {e}")
        return None