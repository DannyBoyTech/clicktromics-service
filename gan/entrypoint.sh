#!/bin/sh
set -e

echo "Environment vars:"
env | grep -E 'INPUT|OUTPUT|BUCKET'

python3 app.py "$INPUT" "$OUTPUT" "$BUCKET" 

