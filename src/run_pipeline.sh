#!/usr/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_CFG="$SCRIPT_DIR/../config/config.yaml"
CONFIG_PATH="${1:-${TEL_MEGIDDO_CONFIG:-$DEFAULT_CFG}}"

export TEL_MEGIDDO_CONFIG="$CONFIG_PATH"

"$SCRIPT_DIR/download_taxonomy.sh" "$CONFIG_PATH"

python "$SCRIPT_DIR/download_genomes.py" --config "$CONFIG_PATH"
python "$SCRIPT_DIR/tag_fasta_headers.py" --config "$CONFIG_PATH"
python "$SCRIPT_DIR/kraken_library.py" --config "$CONFIG_PATH"
python "$SCRIPT_DIR/bracken_build.py" --config "$CONFIG_PATH"

echo "Pipeline complete."
