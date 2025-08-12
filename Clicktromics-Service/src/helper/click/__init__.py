from .click_drug import ClickDrug
from .click_spacc import ClickSPACC
from .click_spacc import ClickSPACCWithoutGlycan
from .click_peptide import ClickPeptide
from rdkit import Chem
from rdkit.Chem import rdChemReactions

# SMILES template for amino acids (N-terminal: NH2, C-terminal: COOH)
amino_acid_blocks = {
    'A': 'N[C@@H](C)C(=O)O',  # Alanine
    'C': 'N[C@@H](CS)C(=O)O',  # Cysteine
    'D': 'N[C@@H](CC(=O)O)C(=O)O',  # Aspartic acid
    'E': 'N[C@@H](CCC(=O)O)C(=O)O',  # Glutamic acid
    'F': 'N[C@@H](Cc1ccccc1)C(=O)O',  # Phenylalanine
    'G': 'NCC(=O)O',  # Glycine
    'H': 'N[C@@H](Cc1c[nH]cn1)C(=O)O',  # Histidine
    'I': 'N[C@@H](CC(C)C)C(=O)O',  # Isoleucine
    'K': 'N[C@@H](CCCCN)C(=O)O',  # Lysine
    'L': 'N[C@@H](CC(C)C)C(=O)O',  # Leucine
    'M': 'N[C@@H](CCSC)C(=O)O',  # Methionine
    'N': 'N[C@@H](CC(=O)N)C(=O)O',  # Asparagine
    'P': 'N1CCC[C@H]1C(=O)O',  # Proline
    'Q': 'N[C@@H](CCC(=O)N)C(=O)O',  # Glutamine
    'R': 'N[C@@H](CCCNC(N)=N)C(=O)O',  # Arginine
    'S': 'N[C@@H](CO)C(=O)O',  # Serine
    'T': 'N[C@@H](C(O)C)C(=O)O',  # Threonine
    'V': 'N[C@@H](C(C)C)C(=O)O',  # Valine
    'W': 'N[C@@H](Cc1c2ccccc2[nH]c1)C(=O)O',  # Tryptophan
    'Y': 'N[C@@H](Cc1ccc(O)cc1)C(=O)O',  # Tyrosine
}

# Pre-convert SMILES to RDKit molecules for efficiency
amino_acid_mols = {k: Chem.MolFromSmiles(v) for k, v in amino_acid_blocks.items()}
for k, mol in amino_acid_mols.items():
    if mol is None:
        raise ValueError(f"Invalid SMILES for amino acid {k}: {amino_acid_blocks[k]}")

def form_peptide_bond(mol1, mol2):
    """
    Form a peptide bond between two amino acid molecules.
    
    Args:
        mol1: RDKit molecule with C-terminal COOH
        mol2: RDKit molecule with N-terminal NH2
    
    Returns:
        RDKit molecule with peptide bond formed, or None if reaction fails
    """
    rxn = rdChemReactions.ReactionFromSmarts('[C:1](=O)O.[N:2]>>[C:1](=O)[N:2]')
    products = rxn.RunReactants((mol1, mol2))
    
    if not products:
        return None
    
    # Take the first product and sanitize
    product = products[0][0]
    try:
        Chem.SanitizeMol(product)
        return product
    except:
        return None

def fasta_to_peptide_smiles(seq, return_mol=False):
    """
    Convert a FASTA sequence to a peptide SMILES string.
    
    Args:
        seq: String of amino acid single-letter codes (e.g., 'AGK')
        return_mol: If True, return RDKit molecule instead of SMILES
    
    Returns:
        Canonical SMILES string or RDKit molecule if return_mol=True
    
    Raises:
        ValueError: If sequence is invalid or too short
    """
    seq = seq.upper().strip()
    if not seq:
        raise ValueError("Sequence cannot be empty.")
    if len(seq) < 1:
        raise ValueError("Peptide must be at least 1 amino acid long.")
    
    # Validate amino acids
    invalid_aas = set(seq) - set(amino_acid_blocks.keys())
    if invalid_aas:
        raise ValueError(f"Invalid amino acid codes: {invalid_aas}")
    
    # Start with first amino acid
    mol = Chem.Mol(amino_acid_mols[seq[0]])  # Copy to avoid modifying original
    
    # Form peptide bonds for subsequent amino acids
    for aa in seq[1:]:
        next_mol = Chem.Mol(amino_acid_mols[aa])
        mol = form_peptide_bond(mol, next_mol)
        if mol is None:
            raise ValueError(f"Failed to form peptide bond with amino acid {aa}")
    
    # Sanitize final molecule
    try:
        Chem.SanitizeMol(mol)
    except:
        raise ValueError("Failed to sanitize final peptide molecule")
    
    if return_mol:
        return mol
    return Chem.MolToSmiles(mol, canonical=True)