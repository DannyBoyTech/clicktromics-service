from rdkit import Chem
from rdkit.Chem import AllChem, QED
from src.config import SMART_REACTION, GLYCAN_LINKER
from src.logger import Logger

logger = Logger.get_logger()

# Function to precisely attach star to N-terminal using SMARTS
def attach_star_to_n_terminal(peptide_smiles):
    mol = Chem.MolFromSmiles(peptide_smiles)
    rw_mol = Chem.RWMol(mol)

    # Precise SMARTS for free NH2 at the peptide N-terminus
    pattern = Chem.MolFromSmarts('[N;H2][C]')
    matches = mol.GetSubstructMatches(pattern)

    if not matches:
        raise ValueError("N-terminal NH2 not found by SMARTS.")
    
    n_idx = matches[0][0]

    # Add star atom
    star_idx = rw_mol.AddAtom(Chem.Atom("*"))
    rw_mol.AddBond(n_idx, star_idx, Chem.BondType.SINGLE)

    # Final SMILES with star
    starred_smiles = Chem.MolToSmiles(rw_mol, isomericSmiles=True, canonical=False)
    starred_smiles = starred_smiles.replace("*", "(*)").replace("((*))", "(*)")
    return starred_smiles


def find_terminal_free_ON_atoms(mol):
    terminal_atoms = []
    # Compute Gasteiger partial charges for the molecule
    AllChem.ComputeGasteigerCharges(mol)
    for atom in mol.GetAtoms():
        if atom.HasProp('_GasteigerCharge'):
            charge = float(atom.GetProp('_GasteigerCharge'))
            # Check for terminal oxygen atoms (degree 1)
            if atom.GetSymbol() == 'O' and atom.GetDegree() == 1:
                terminal_atoms.append({"symbol": atom.GetSymbol(), 'Number': atom.GetIdx(), 'PartialCharge': charge})
            # Check for nitrogen atoms with degree 1 or 2
            elif atom.GetSymbol() == 'N' and atom.GetDegree() <= 2:
                terminal_atoms.append({"symbol": atom.GetSymbol(), 'Number': atom.GetIdx(), 'PartialCharge': charge})
    return terminal_atoms

def positions(smiles):
    # Convert SMILES string to RDKit molecule
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return []

    # Find terminal O and N atoms
    terminal_atoms = find_terminal_free_ON_atoms(mol)
    new_smiles_list = []

    for on_idx in terminal_atoms:
        # Process only atoms with negative partial charge
        if on_idx['PartialCharge'] < 0:
            # Create editable molecule copy
            rw_mol = Chem.RWMol(mol)
            rw_mol.UpdatePropertyCache(strict=False)
            Chem.FastFindRings(rw_mol)

            # Add a dummy atom (*)
            star_atom_idx = rw_mol.AddAtom(Chem.Atom('*'))
            # Add single bond between selected atom and dummy atom
            rw_mol.AddBond(on_idx['Number'], star_atom_idx, Chem.BondType.SINGLE)

            # Convert modified molecule to SMILES
            new_smiles = Chem.MolToSmiles(rw_mol, isomericSmiles=True, canonical=False)
            # Replace dummy atom notation
            new_smiles = new_smiles.replace('*', '(*)').replace('((*))', '(*)')

            # Replace [nH] with N if present
            if '[nH]' in new_smiles:
                new_smiles = new_smiles.replace('[nH]', 'N')

            new_smiles_list.append({
                "SMILES": new_smiles,
                "PartialCharge": on_idx['PartialCharge']
            })

    return new_smiles_list


def evaluate_clickable_variants(drug_variants, scaffold_smiles):
    combined_molecules = []

    for variant in drug_variants:
        # Combine scaffold with starred drug variant
        combined_smiles = scaffold_smiles + '.' + variant['SMILES']
        # Replace placeholder (*) with atom number 9
        combined_smiles = combined_smiles.replace('(*)', '9')

        # Convert combined SMILES to RDKit molecule
        mol = Chem.MolFromSmiles(combined_smiles)
        if mol:
            try:
                # Calculate QED (Quantitative Estimate of Drug-likeness) score
                qed_score = QED.qed(mol)
                combined_molecules.append({
                    "SMILES": Chem.MolToSmiles(mol),
                    "QED": qed_score,
                    "PartialCharge": variant['PartialCharge'],
                    "MOL": mol
                })
            except:
                # Skip if QED calculation fails
                continue

    # Sort molecules by QED score in descending order
    return sorted(combined_molecules, key=lambda x: x["QED"], reverse=True)


# ⚙️ Construct linker + azide compound
def build_linker_azide(core_smiles, azide_smiles):
    combined = core_smiles + '.' + azide_smiles
    combined = combined.replace('(*)', '9')
    mol = Chem.MolFromSmiles(combined)
    return Chem.MolToSmiles(mol)

# ⚙️ Perform Click reaction
def run_click_reaction(drug_smiles, linker_core, azide_smiles, reaction_smarts):
    linker_azide = build_linker_azide(linker_core, azide_smiles)
    drug_mol = Chem.MolFromSmiles(drug_smiles)
    linker_mol = Chem.MolFromSmiles(linker_azide)
    rxn = AllChem.ReactionFromSmarts(reaction_smarts)
    products = rxn.RunReactants([drug_mol, linker_mol])
    if not products:
        raise ValueError("❌ Reaction failed: No product generated.")
    return Chem.MolToSmiles(products[0][0]).replace("(*)", "")

def replace_first_c_with_c_star(smiles):
    """
    Replace the first occurrence of 'C' in the SMILES string with 'C(*)'.

    :param smiles: str, original SMILES string
    :return: str, updated SMILES string
    """
    return smiles.replace('C', 'C(*)', 1)

def ClickPeptide(drug, peptide, peptide_linker, drug_linker):
    logger.info(drug)
    logger.info( peptide)
    logger.info(peptide_linker)
    logger.info(drug_linker)

    starred_peptide = attach_star_to_n_terminal(peptide)
    logger.info(starred_peptide)
    
    smi3 = f'{starred_peptide}.{peptide_linker}'
    smi24 = smi3.replace('(*)', '9')
    mol24 = Chem.MolFromSmiles(smi24)
    linker_core = Chem.MolToSmiles(mol24)
    #ONLY AND ONLY FOR THE CURRENT PEPTIDE LINKER, OTHER LINKERS NEED TESTING
    linker_core = replace_first_c_with_c_star(linker_core)

    logger.info(linker_core)

    starred_drug_smiles_list = positions(drug)

    for i, variant in enumerate(starred_drug_smiles_list):
        logger.info(f"Variant {i + 1}: SMILES: {variant['SMILES']}, PartialCharge: {variant['PartialCharge']:.3f}")

    sorted_combined = evaluate_clickable_variants(starred_drug_smiles_list, drug_linker)
    best_smiles = sorted_combined[0]
    logger.info(best_smiles)
    logger.info(GLYCAN_LINKER["Azide"])
    logger.info(SMART_REACTION["SPACC"])


    final_smiles = run_click_reaction(
        drug_smiles=best_smiles["SMILES"],
        linker_core=linker_core,
        azide_smiles=GLYCAN_LINKER["Azide"],
        reaction_smarts=SMART_REACTION["SPACC"]
    )

    return final_smiles