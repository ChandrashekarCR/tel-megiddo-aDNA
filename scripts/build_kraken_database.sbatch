#!/usr/bin/bash
#SBATCH --job-name=kraken_bracken
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/home/chandru/tel-megiddo/logs/kraken_bracken_%j.out
#SBATCH --error=/home/chandru/tel-megiddo/logs/kraken_bracken_%j.err

set -euo pipefail
mkdir -p /home/chandru/tel-megiddo/logs

# Load conda and run
export BASHRCSOURCED=1
source ~/.bashrc
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate tel-megiddo
fi

# Run this bash script
/home/chandru/tel-megiddo/src/db_build/run.sh