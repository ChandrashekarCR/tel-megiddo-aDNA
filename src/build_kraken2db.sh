#!/usr/bin/bash

set -euo pipefail

# Environment name
CONDA_ENV_NAME="tel-megiddo"

# GLOBAL VARIABLES
DB_DIR="/home/chandru/lu2025-12-38/Students/chandru/tel-meggido/kraken2_telmegiddo_db"
SCRIPT_DIR="$(dirname "$0")"
LOG_DIR="$SCRIPT_DIR/../logs"
THREADS=16

printf "%.0s=" {1..40}
printf "\n"
echo "Setting up kraken and bracken database"
printf "%.0s=" {1..40}
printf "\n"


# 1. Install dependencies
echo "[1/6] Installing dependencies"
if conda env list | grep -q "$CONDA_ENV_NAME"; then \
    # Activate conda environment
    eval "$(conda shell.bash hook)" # Attach the terminal to conda environment. This step is crucial for the script to run.
    conda activate "$CONDA_ENV_NAME"

    # Check if kraken and bracken are installed
    if ! command -v kraken2 >/dev/null 2>&1 || ! command -v bracken >/dev/null 2>&1; then \
        echo "Error: kraken and/or bracken are not installed in the $CONDA_ENV_NAME environment."
        echo "Please install via the make conda_env command and re-run the script."
        exit 0
    fi

    echo "kraken2 and bracken are installed."
    echo "$(which kraken2)"
    echo "$(which bracken)"
else
    echo "Conda environemt $CONDA_ENV_NAME does not exist."
    echo "Please install via the make conda_env command and re-run the script."
    exit 0

fi

# 2. Build the Kraken2 database
echo "[2/6] Building the kraken2 database"
mkdir -p $DB_DIR
 
if [ ! -f "$DB_DIR/taxonomy/nodes.dmp" ]; then

    echo "Downloading the taxonomy database.";
        wget -c "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz" \
             -P "$DB_DIR/taxonomy/" \
             >> "$LOG_DIR/taxonomy.log" 2>&1

        wget -c "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz" \
             -P "$DB_DIR/taxonomy/" \
             >> "$LOG_DIR/taxonomy.log" 2>&1

        wget -c "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.gz" \
             -P "$DB_DIR/taxonomy/" \
             >> "$LOG_DIR/taxonomy.log" 2>&1;

    echo "Extracting..."
    tar -xzf "$DB_DIR/taxonomy/taxdump.tar.gz" -C "$DB_DIR/taxonomy/"
    gunzip "$DB_DIR/taxonomy/nucl_gb.accession2taxid.gz"
    gunzip "$DB_DIR/taxonomy/nucl_wgs.accession2taxid.gz"

    echo "Done. Log: $LOG_DIR/taxonomy.log"
else
    echo "Taxonomy already present, skipping."
fi