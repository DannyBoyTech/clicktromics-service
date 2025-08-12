import torch
import numpy as np
import boto3
import logging
import json
import sys
import tempfile
import os
import botocore.exceptions
from transformers import AutoTokenizer, AutoModelForMaskedLM
from torch.distributions.categorical import Categorical
from typing import Tuple, List, Dict, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BUCKET_NAME = "clicktromics"
MODEL_NAME = "ChatterjeeLab/PepMLM-650M"

def load_model_and_tokenizer(model_name: str) -> Tuple[AutoTokenizer, AutoModelForMaskedLM]:
    """Load the transformer model and tokenizer."""
    try:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Loading model {model_name} on {device}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForMaskedLM.from_pretrained(model_name).to(device)
        return tokenizer, model
    except Exception as e:
        logger.error(f"Failed to load model or tokenizer: {e}")
        raise

# Load model and tokenizer at startup
try:
    tokenizer, model = load_model_and_tokenizer(MODEL_NAME)
except Exception:
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

def compute_pseudo_perplexity(model: AutoModelForMaskedLM, tokenizer: AutoTokenizer, protein_seq: str, binder_seq: str) -> float:
    """Compute the pseudo perplexity for a given protein-binder sequence."""
    try:
        sequence = protein_seq + binder_seq
        original_input = tokenizer.encode(sequence, return_tensors='pt').to(model.device)
        binder_length = len(binder_seq)

        # Prepare a batch where each row has one masked token from the binder sequence
        masked_inputs = original_input.repeat(binder_length, 1)
        positions_to_mask = torch.arange(-binder_length - 1, -1, device=model.device)
        masked_inputs[torch.arange(binder_length), positions_to_mask] = tokenizer.mask_token_id

        # Prepare labels for the masked tokens
        labels = torch.full_like(masked_inputs, -100)
        labels[torch.arange(binder_length), positions_to_mask] = original_input[0, positions_to_mask]

        # Compute loss and pseudo perplexity
        with torch.no_grad():
            loss = model(masked_inputs, labels=labels).loss
        return np.exp(loss.item())
    except Exception as e:
        logger.error(f"Error computing pseudo perplexity: {e}")
        raise

def generate_peptide_for_single_sequence(
    protein_seq: str,
    peptide_length: int,
    top_k: int,
    num_binders: int,
    model: AutoModelForMaskedLM,
    tokenizer: AutoTokenizer
) -> List[Dict]:
    """Generate peptide sequences for a single protein sequence."""
    try:
        binders_with_ppl = []
        for _ in range(num_binders):
            # Generate masked peptide
            masked_peptide = "<mask>" * peptide_length
            input_sequence = protein_seq + masked_peptide
            inputs = tokenizer(input_sequence, return_tensors="pt").to(model.device)

            with torch.no_grad():
                logits = model(**inputs).logits

            mask_token_indices = (inputs["input_ids"] == tokenizer.mask_token_id).nonzero(as_tuple=True)[1]
            logits_at_masks = logits[0, mask_token_indices]

            # Apply top-k sampling
            top_k_logits, top_k_indices = logits_at_masks.topk(top_k, dim=-1)
            probabilities = torch.nn.functional.softmax(top_k_logits, dim=-1)
            predicted_indices = Categorical(probabilities).sample()
            predicted_token_ids = top_k_indices.gather(-1, predicted_indices.unsqueeze(-1)).squeeze(-1)

            generated_binder = tokenizer.decode(predicted_token_ids, skip_special_tokens=True).replace(' ', '')
            ppl_value = compute_pseudo_perplexity(model, tokenizer, protein_seq, generated_binder)
            binders_with_ppl.append({"binder": generated_binder, "pseudo_perplexity": ppl_value})

        return binders_with_ppl
    except Exception as e:
        logger.error(f"Error generating peptide for sequence: {e}")
        raise

def generate_peptide(
    input_seqs: Union[str, List[str]],
    peptide_length: int,
    top_k: int,
    num_binders: int,
    model: AutoModelForMaskedLM,
    tokenizer: AutoTokenizer
) -> List[Dict]:
    """Generate peptide sequences for single or multiple input sequences."""
    try:
        if not isinstance(peptide_length, int) or peptide_length <= 0:
            raise ValueError("peptide_length must be a positive integer")
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        if not isinstance(num_binders, int) or num_binders <= 0:
            raise ValueError("num_binders must be a positive integer")

        results = []
        input_seqs = [input_seqs] if isinstance(input_seqs, str) else input_seqs
        if not all(isinstance(seq, str) and seq for seq in input_seqs):
            raise ValueError("All input sequences must be non-empty strings")

        for seq in input_seqs:
            binders = generate_peptide_for_single_sequence(seq, peptide_length, top_k, num_binders, model, tokenizer)
            for binder in binders:
                results.append({
                    "input_sequence": seq,
                    "binder": binder["binder"],
                    "pseudo_perplexity": binder["pseudo_perplexity"]
                })
        return results
    except Exception as e:
        logger.error(f"Error generating peptides: {e}")
        raise

def main(input_file: str, output_file: str, s3_bucket: str) -> None:
    """Generate peptides for protein sequences and upload results to S3."""
    try:
        if not all([input_file, s3_bucket, output_file]):
            raise ValueError("All command-line arguments (INPUT_KEY, OUTPUT_KEY, BUCKET) must be provided.")

        with tempfile.TemporaryDirectory() as temp_dir:
            json_file = os.path.join(temp_dir, "input.json")
            output_json = os.path.join(temp_dir, "output.json")

            # Download and validate JSON input
            download(input_file, json_file, s3_bucket)
            logger.info("JSON input file downloaded successfully")
            with open(json_file, 'r') as f:
                protein_data = json.load(f)
            required_keys = ['protein_seq', 'peptide_length', 'top_k', 'num_binders']
            if not all(k in protein_data for k in required_keys):
                raise ValueError(f"JSON data must contain {required_keys} keys")
            if not isinstance(protein_data['protein_seq'], (str, list)) or not protein_data['protein_seq']:
                raise ValueError("protein_seq must be a non-empty string or list of strings")

            # Generate peptides
            results = generate_peptide(
                input_seqs=protein_data["protein_seq"],
                peptide_length=protein_data["peptide_length"],
                top_k=protein_data["top_k"],
                num_binders=protein_data["num_binders"],
                model=model,
                tokenizer=tokenizer
            )
            logger.info(f"Generated {len(results)} peptide binders")

            # Extract scores and binders
            scores = [result["pseudo_perplexity"] for result in results]
            binders = [result["binder"] for result in results]

            if not scores:
                logger.error("No scores found in results.")
                raise ValueError("No scores found in results.")

            min_score = float('inf')
            best = -1
            for i, score in enumerate(scores):
                if score < min_score:
                    min_score = score
                    best = i

            if best == -1:
                logger.error("Failed to determine the best score.")
                raise ValueError("Failed to determine the best score.")

            best_res = binders[best]
            if 'X' in best_res:
                best_res = best_res.replace('X', 'A')

            output = {
                "sequence": best_res,
                "uncertainty_score": min_score
            }
            # Write JSON output
            with open(output_json, 'w') as f:
                json.dump(output, f, indent=4)
            logger.info("JSON output written")

            # Upload results to S3
            upload(output_json, output_file, s3_bucket)
            logger.info("Output file uploaded successfully")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python app.py <INPUT_KEY> <OUTPUT_KEY> <BUCKET>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])