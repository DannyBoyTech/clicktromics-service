import warnings
import re
import os
import yaml
import boto3
import logging
import json
import sys
import tempfile
import subprocess
import botocore.exceptions
from openbabel import pybel
from rdkit import Chem
import MDAnalysis as mda

# Suppress warnings from MDAnalysis
warnings.filterwarnings("ignore", category=UserWarning, module="MDAnalysis")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
BUCKET_NAME = "clicktromics"

# Load configuration from YAML file
try:
    with open(os.path.join(os.getcwd(), "config.yaml"), "r") as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    logger.error("Configuration file 'config.yaml' not found in current directory.")
    sys.exit(1)
except yaml.YAMLError as e:
    logger.error(f"Error parsing config.yaml: {e}")
    sys.exit(1)

def download_from_s3(local_file: str, object_key: str, bucket: str) -> None:
    """Download a file from S3 to the specified local path."""
    s3 = boto3.client('s3')
    logger.info(f"Downloading s3://{bucket}/{object_key} to {local_file}")
    try:
        s3.download_file(bucket, object_key, local_file)
    except botocore.exceptions.ClientError as e:
        logger.error(f"Failed to download from S3: {e}")
        raise

def upload_to_s3(local_file: str, object_key: str, bucket: str) -> None:
    """Upload a file to S3 from the specified local path."""
    s3 = boto3.client('s3')
    logger.info(f"Uploading {local_file} to s3://{bucket}/{object_key}")
    try:
        s3.upload_file(local_file, bucket, object_key)
    except botocore.exceptions.ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        raise

def download_from_local(src_path: str, dest_path: str) -> None:
        logger.info(f"LocalAdapter: Copying {src_path} → {dest_path}")
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Local file not found: {src_path}")
        with open(src_path, "rb") as sf, open(dest_path, "wb") as df:
            df.write(sf.read())

def upload_to_local(src_path: str, dst_path: str) -> None:
        dir_path = os.path.dirname(dst_path)
        os.makedirs(dir_path, exist_ok=True)

        logger.info(f"LocalAdapter: Copying {src_path} → {dst_path}")
        with open(src_path, "rb") as sf, open(dst_path, "wb") as df:
            df.write(sf.read())

def download(source: str, dest_path: str, bucket: str) -> None:
    try:
        download_from_s3(source, dest_path, bucket)
    except Exception as e:
        logger.warning(f"Primary download failed ({e}), trying fallback…")
        download_from_local(source, dest_path)

def upload(src_path: str, dest: str, bucket: str) -> None:
        try:
            upload_to_s3(src_path, dest, bucket)
        except Exception as e:
            logger.warning(f"Primary upload failed ({e}), trying fallback…")
            upload_to_local(src_path, dest)

def chain_finder(pdb_file_path: str, res_number: str) -> str:
    """Find the chain ID for a given residue number in a PDB file."""
    with open(pdb_file_path) as f:
        chains = {
            line[21].strip()
            for line in f
            if line.startswith('ATOM') and line[22:26].strip() == str(res_number)
        }
    if len(chains) != 1:
        raise ValueError(f"Expected exactly one chain for residue {res_number}, found {chains}")
    return chains.pop()

def parse_gnina_output(log_file: str) -> str:
    """Parse Gnina output log to extract the affinity value."""
    try:
        with open(log_file, 'r') as f:
            log_content = f.read()
        pattern = r'^\s*\d+\s+(-?\d+\.\d+)\s+'
        matches = re.findall(pattern, log_content, re.MULTILINE)
        return matches[0] if matches else ""
    except FileNotFoundError:
        logger.error(f"Log file not found: {log_file}")
        raise
    except Exception as e:
        logger.error(f"Error parsing Gnina output: {e}")
        raise

def select_best_model(input_file: str, output_file: str) -> None:
    """Select the best model from Gnina output based on minimized affinity."""
    with open(input_file, 'r') as f:
        content = f.read()
    models = re.findall(r'(MODEL.*?ENDMDL)', content, re.DOTALL)
    if not models:
        raise ValueError("No models found in Gnina output")
    affinities = [float(model.split('\n')[1].split(' ')[-1]) for model in models]
    best_model = models[affinities.index(min(affinities))]
    with open(output_file, "w") as f:
        f.write(best_model)

def merge_molecules(pdb_file: str, model_file: str, output_file: str) -> None:
    """Merge two molecular structures into a single PDB file."""
    u1 = mda.Universe(pdb_file)
    u2 = mda.Universe(model_file)
    merged = mda.Merge(u1.atoms, u2.atoms)
    merged.atoms.write(output_file)

    """Process PDB and SMILES data, perform docking with Gnina, and upload results to S3."""
def main(input_file: str, json_input_file: str,  output_file: str, json_output_file: str, s3_bucket: str) -> None:
    try:
        if not all([json_input_file, s3_bucket, input_file, output_file, json_output_file]):
            raise ValueError("All command-line arguments (INPUT, INPUT_JSON, OUTPUT, OUTPUT_JSON, BUCKET) must be provided.")

        with tempfile.TemporaryDirectory() as temp_dir:
            json_file = os.path.join(temp_dir, "input.json")
            pdb_file = os.path.join(temp_dir, "input.pdb")
            mol_file = os.path.join(temp_dir, "ComplexSmile.mol")
            gnina_output = os.path.join(temp_dir, "gnina_output.pdb")
            model_file = os.path.join(temp_dir, "docking_model.pdb")
            final_output = os.path.join(temp_dir, "output.pdb")
            output_json = os.path.join(temp_dir, "output.json")
            log_file = os.path.join(temp_dir, "gnina.log")

            # Download and validate JSON input
            download(json_input_file, json_file, s3_bucket)
            logger.info("JSON input file downloaded successfully")
            with open(json_file, 'r') as f:
                protein_data = json.load(f)
            required_keys = ['resNumber', 'spacc']
            if not all(k in protein_data for k in required_keys):
                raise ValueError(f"JSON data must contain {required_keys} keys")
            if os.path.getsize(json_file) > MAX_FILE_SIZE:
                raise ValueError(f"Input file size exceeds {MAX_FILE_SIZE / (1024 * 1024)} MB")

            # Download PDB file
            download(input_file, pdb_file, s3_bucket)
            logger.info("PDB file downloaded successfully")
            if not os.path.exists(pdb_file):
                raise FileNotFoundError("PDB file not found after download")

            # Determine chain and atom
            res_number = str(protein_data['resNumber'])
            chain = chain_finder(pdb_file, res_number)
            atom_name = "ND2"  # Default for covalent docking
            if not res_number:
                with open(pdb_file) as f:
                    for line in f:
                        if line.startswith('ATOM') and line[12:16].strip().upper() == 'N':
                            chain = line[21].strip()
                            res_number = line[22:26].strip()
                            atom_name = line[12:16].strip()
                            break
                if not chain:
                    raise ValueError("Could not determine chain from PDB file")

            # Process SMILES and generate MOL file
            spacc_mol = Chem.MolFromSmiles(protein_data['spacc'])
            if not spacc_mol:
                raise ValueError("Invalid SMILES string")
            Chem.MolToMolFile(spacc_mol, mol_file)
            mol = next(pybel.readfile('mol', mol_file))
            mol.addh()
            mol.write("mol", mol_file, overwrite=True)
            logger.info("MOL file generated successfully")

            # Run Gnina
            cmd = [
                os.path.join(os.getcwd(), config['Paths']['GninaFile']),
                '-r', pdb_file,
                '-l', mol_file,
                '--autobox_ligand', pdb_file,
                '-o', gnina_output,
                '--covalent_rec_atom', f'{chain}:{res_number}:{atom_name}',
                '--covalent_lig_atom_pattern',
                config['SmartReactions']['Gnina_PDC'] if atom_name != "ND2" else config['SmartReactions']['Gnina_ADC']
            ]
            with open(log_file, 'w') as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True, text=True)
            logger.info("Gnina docking completed")

            # Parse Gnina output
            affinity = parse_gnina_output(log_file)
            if not affinity:
                logger.warning("No affinity value found in Gnina output")

            # Select best model
            if not os.path.exists(gnina_output):
                raise FileNotFoundError("Gnina output file not found")
            select_best_model(gnina_output, model_file)
            logger.info("Best model selected")

            # Merge molecules
            merge_molecules(pdb_file, model_file, final_output)
            logger.info("Molecules merged successfully")

            # Write JSON output
            with open(output_json, 'w') as f:
                json.dump({"affinity": affinity}, f, indent=4)
            logger.info("JSON output written")

            # Upload results to S3
            upload(final_output, output_file, s3_bucket)
            upload(output_json, json_output_file, s3_bucket)
            logger.info("Files uploaded successfully")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python app.py <INPUT> <INPUT_JSON> <OUTPUT> <OUTPUT_JSON> <BUCKET>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])