#!/usr/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_CFG="$SCRIPT_DIR/../config/config.yaml"
CONFIG_PATH="${1:-${TEL_MEGIDDO_CONFIG:-$DEFAULT_CFG}}"

read -r DB_DIR LOG_DIR < <(
python - <<'PY'
import os
import sys
from omegaconf import OmegaConf

cfg_path = sys.argv[1]
config = OmegaConf.load(cfg_path)
print(config.database, config.log_dir)
PY
"$CONFIG_PATH"
)

mkdir -p "$DB_DIR" "$LOG_DIR" "$DB_DIR/taxonomy"

if [ ! -f "$DB_DIR/taxonomy/nodes.dmp" ]; then
  echo "Downloading taxonomy via HTTPS."
  wget -c "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz" \
       -P "$DB_DIR/taxonomy/" \
       >> "$LOG_DIR/taxonomy.log" 2>&1

  wget -c "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz" \
       -P "$DB_DIR/taxonomy/" \
       >> "$LOG_DIR/taxonomy.log" 2>&1

  wget -c "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.gz" \
       -P "$DB_DIR/taxonomy/" \
       >> "$LOG_DIR/taxonomy.log" 2>&1

  echo "Extracting taxonomy archives..."
  tar -xzf "$DB_DIR/taxonomy/taxdump.tar.gz" -C "$DB_DIR/taxonomy/"
  gunzip -f "$DB_DIR/taxonomy/nucl_gb.accession2taxid.gz"
  gunzip -f "$DB_DIR/taxonomy/nucl_wgs.accession2taxid.gz"

  echo "Taxonomy download complete. Log: $LOG_DIR/taxonomy.log"
else
  echo "Taxonomy already present, skipping."
fi
