from rdkit import Chem
from rdkit.Chem import AllChem, QED
# import pandas as pd
import random


# Function to find terminal free oxygen or nitrogen atoms
def find_terminal_free_ON_atoms(mol):
    terminal_atoms = []
    AllChem.ComputeGasteigerCharges(mol)
    for atom in mol.GetAtoms():
        if atom.GetSymbol() == 'O' and atom.GetDegree() == 1:  # Oxygen atoms with one bond
            terminal_atoms.append({"symbol":atom.GetSymbol(),'Number':atom.GetIdx(),'PartialCharge':float(atom.GetProp('_GasteigerCharge'))})
        elif atom.GetSymbol() == 'N' and atom.GetDegree() >=2:
            terminal_atoms.append({"symbol":atom.GetSymbol(),'Number':atom.GetIdx(),'PartialCharge':float(atom.GetProp('_GasteigerCharge'))})
    return terminal_atoms

# Calculate QED for clicked drugs
def qed(list_smiles):
    new_mols = [{'MOL':Chem.MolFromSmiles(smiles['SMILES']),"SMILES":smiles['SMILES'],"PartialCharge":smiles['PartialCharge'],'Linker':smiles["Linker"],'Linker_name':smiles["Linker_name"] } for smiles in list_smiles if Chem.MolFromSmiles(smiles['SMILES']) is not None]
    mols_with_qed = [{"QED":QED.qed(mol['MOL']),"SMILES":mol['SMILES'],"PartialCharge":mol['PartialCharge'],'Linker':mol["Linker"], 'Linker_name':mol["Linker_name"]} for mol in new_mols]
    mols_with_qed.sort(key=lambda x: x["QED"], reverse=True)
    return mols_with_qed


def reaction(drug_smiles,clickable_st_smile, linker_name):
    smis=[]
    for smiles in drug_smiles : 
        try:
            smi = clickable_st_smile+'.'+smiles['SMILES']
            mol = Chem.MolFromSmiles(smi.replace('(*)', '9'))
            new_smi = Chem.MolToSmiles(mol,isomericSmiles=True, canonical=False)
        except:
            new_smi = None
        if new_smi:
            smis.append({"SMILES":new_smi,"PartialCharge":smiles['PartialCharge'],"Linker":clickable_st_smile, "Linker_name": linker_name})
    return smis

def ClickDrug(smiles,linkers):
    if '*' not in smiles:
        # Convert SMILES to molecule
        mol = Chem.MolFromSmiles(smiles)

        # Find terminal free O-N atoms
        terminal_atoms = find_terminal_free_ON_atoms(mol)

        # List of new SMILES
        new_smiles_list = []

        if terminal_atoms:
            for info in terminal_atoms:
                if info['PartialCharge'] < 0:
                    # Add star to each terminal oxygen and nitrogen atom found
                    rw_mol = Chem.RWMol(mol)
                    rw_mol.UpdatePropertyCache(strict=False)
                    Chem.FastFindRings(rw_mol)
                    star_atom_idx = rw_mol.AddAtom(Chem.Atom('*'))  # Add star atom
                    rw_mol.AddBond(info['Number'], star_atom_idx, Chem.BondType.SINGLE)  # Add bond between star atom and terminal oxygen or nitrogen atom

                    # Convert molecule to new SMILES, keeping the original atom order
                    new_smiles = Chem.MolToSmiles(rw_mol, isomericSmiles=True, canonical=False)
                    new_smiles = new_smiles.replace('*','(*)')
                    new_smiles = new_smiles.replace('((*))','(*)')
                    new_smiles_list.append({"SMILES":new_smiles,"PartialCharge":info['PartialCharge']})
        else:
            assert False, 'No suitable terminal oxygen or Nitrogen atoms found to add the star atom.'
    else:
        new_smiles_list = [{"SMILES":smiles,"PartialCharge":None}]

    smis = []
    for key,value in linkers.items():
        smis.extend(reaction(new_smiles_list,value, key))
    
    if len(smis) == 0:
        assert False, "Drug Is Not Clickable Structure"

    mol_with_qed = qed(smis)
    if len(mol_with_qed) > 1:
        # scores = [(clicked_drug['PartialCharge'] - clicked_drug['QED']) for clicked_drug in mol_with_qed]
        # clicked = mol_with_qed[pd.Series(scores).idxmin()]
        clicked = random.choice(mol_with_qed)
    return clicked