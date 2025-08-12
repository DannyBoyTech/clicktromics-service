from rdkit import Chem
from rdkit.Chem import AllChem
import re

def GlycanAzide(smile_1,smile_2):
    smiles = smile_1+'.'+smile_2
    new_smile = smiles.replace('(*)', '9')
    m = Chem.MolFromSmiles(new_smile)
    smile = Chem.MolToSmiles(m)
    return smile

def spacc_reaction(reactants,smart_reaction):
    rxn = AllChem.ReactionFromSmarts(smart_reaction)
    predicted_products_list = rxn.RunReactants(reactants)
    smiles = Chem.MolToSmiles(predicted_products_list[0][0])
    return smiles

def ClickSPACC(ComplexDrug, Glycan, GlycanLinker, smart_reaction):
    glycanazide = GlycanAzide(smile_1=Glycan,smile_2=GlycanLinker)
    # convert smiles to mol
    complex_drug_m = Chem.MolFromSmiles(ComplexDrug['SMILES'])
    linker_m = Chem.MolFromSmiles(ComplexDrug['Linker'])
    glycan_azide_m = Chem.MolFromSmiles(glycanazide)
    # run smarts reaction
    spacc = spacc_reaction(reactants=[complex_drug_m,glycan_azide_m],smart_reaction=smart_reaction)
    nanoparticle_linker_star = spacc_reaction(reactants=[linker_m,glycan_azide_m],smart_reaction=smart_reaction)
    return {'SPACC':spacc,'NP_Linker':re.sub(r'\(\*\)|\*', '', nanoparticle_linker_star)}


def ClickSPACCWithoutGlycan(ComplexDrug, DirectLinker, smart_reaction):
    """
    Perform click chemistry (SPACC) without requiring a glycan input.
    
    Parameters:
        ComplexDrug (dict): Dictionary with 'SMILES' and 'Linker' for the complex drug.
        DirectLinker (str): A clickable linker SMILES (e.g., azide or alkyne).
        smart_reaction (str): SMARTS pattern defining the click reaction.

    Returns:
        dict: Contains clicked drug ('SPACC') and modified linker ('NP_Linker').
    """
    # Convert inputs to RDKit Mol objects
    complex_drug_m = Chem.MolFromSmiles(ComplexDrug['SMILES'])
    linker_m = Chem.MolFromSmiles(ComplexDrug['Linker'])
    direct_linker_m = Chem.MolFromSmiles(DirectLinker)

    # Run SMARTS reaction
    spacc = spacc_reaction(reactants=[complex_drug_m, direct_linker_m], smart_reaction=smart_reaction)
    nanoparticle_linker_star = spacc_reaction(reactants=[linker_m, direct_linker_m], smart_reaction=smart_reaction)

    return {
        'SPACC': re.sub(r'\(\*\)|\*', '', spacc),
        'NP_Linker': re.sub(r'\(\*\)|\*', '', nanoparticle_linker_star)
    }
