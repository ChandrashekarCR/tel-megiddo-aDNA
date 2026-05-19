#!/usr/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo $SCRIPT_DIR
CONFIG="$SCRIPT_DIR/../../config/config.yaml"

eval "$(conda shell.bash hook)"
conda activate "tel-megiddo"

# Pass any extra args straight through to Python
# e.g. --builds run_gallus_standard
python "$SCRIPT_DIR/build_db.py" --config "$CONFIG" "$@"