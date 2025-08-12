from Bio import PDB
import sys
from fastapi import UploadFile, HTTPException
import io
from typing import Union, IO
from starlette.datastructures import UploadFile as StarletteUploadFile

ALLOWED_EXTENSION = ".pdb"  # Only allow PDB files
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def read_pdb(pdbcode, pdbfilenm):
    """
    Read a PDB structure from a file.
    :param pdbcode: A PDB ID string
    :param pdbfilenm: The PDB file
    :return: a Bio.PDB.Structure object or None if something went wrong
    """
    try:
        pdbparser = PDB.PDBParser(QUIET=True)  # Suppress PDBConstructionWarning
        struct = pdbparser.get_structure(pdbcode, pdbfilenm)
        return struct
    except Exception as err:
        print(str(err), file=sys.stderr)
        return None


def extract_seqrecords(struct):
    """
    Extracts the sequence records from a Bio.PDB structure.
    :param struct: a Bio.PDB.Structure object
    :return: a tuple (whole sequence as a string)
    """
    ppb = PDB.PPBuilder()
    whole_seq = ""

    for s in ppb.build_peptides(struct):
        whole_seq += str(s.get_sequence())

    return whole_seq

def extract_chains(struct):
    """
    Extracts the sequence records from a Bio.PDB structure.
    :param struct: a Bio.PDB.Structure object
    :return: a tuple (dictionary of chain sequences)
    """
    ppb = PDB.PPBuilder()

    seqrecords = {}
    for chain in struct.get_chains():
        if chain.id == 'L':
            seq = "".join(str(pp.get_sequence()) for pp in ppb.build_peptides(chain))
            seqrecords['light_sequence'] = seq
        elif chain.id == 'H':
            seq = "".join(str(pp.get_sequence()) for pp in ppb.build_peptides(chain))
            seqrecords['heavy_sequence'] = seq
        else:
            continue
    return seqrecords


def convert(file: IO[bytes], type: str):
    try:
        # Read the uploaded file
        contents = file.read()  # Handle synchronous file objects

        # Validate file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE / (1024 * 1024)} MB",
            )

        # Read PDB file using BytesIO
        structure = read_pdb("protein", io.StringIO(contents.decode("utf-8")))

        if structure is None:
            raise HTTPException(status_code=400, detail="Failed to parse the PDB file.")

        if type == "homelette":
            # Get chain sequence
            chains = extract_chains(structure)
            return chains
        elif type == "musite":
            # Get chain sequence
            whole_seq = extract_seqrecords(structure)
            return whole_seq
        else:
            raise HTTPException(status_code=500, detail=f"type {type} not exist.")
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the file: {str(e)}",
        )