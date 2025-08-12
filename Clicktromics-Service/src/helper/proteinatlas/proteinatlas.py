import requests

HPA_API = "https://www.proteinatlas.org/"


def get_tissue_proteins(tissue):
    """Retrieve proteins from HPA"""
    try:
        response = requests.get(f"{HPA_API}api/search_download.php?search=tissue:{tissue}&format=json&columns=Gene,Gene%20name")
        response.raise_for_status()
        return list({entry['Gene'] for entry in response.json()})
    except Exception as e:
        print(f"Error fetching tissue proteins: {e}")
        return []

def get_proteins(esmid):
    """Retrieve proteins from HPA"""
    try:
        response = requests.get(f"{HPA_API}{esmid}.json")
        response.raise_for_status()
        return list({entry['Gene'] for entry in response.json()})
    except Exception as e:
        print(f"Error fetching tissue proteins: {e}")
        return []