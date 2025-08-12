#!/bin/sh
set -e

echo "Environment vars:"
env | grep -E 'INPUT|INPUT_JSON|OUTPUT|OUTPUT_JSON|BUCKET'

python3 run.py "$INPUT" "$INPUT_JSON" "$OUTPUT" "$OUTPUT_JSON" "$BUCKET" 

