#!/usr/bin/bash
#SBATCH --job-name=kraken_bracken
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=/home/chandru/tel-megiddo/logs/kraken_bracken_%j.out
#SBATCH --error=/home/chandru/tel-megiddo/logs/kraken_bracken_%j.err

set -euo pipefail

mkdir -p /home/chandru/tel-megiddo/logs

# Load and activate conda
source ~/.bashrc
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate tel-megiddo
fi

export KRAKEN_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export BRACKEN_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export KRAKEN_KMER="35"
export BRACKEN_READLEN="75"

CONFIG_PATH="/home/chandru/tel-megiddo/config/config.yaml"

/home/chandru/tel-megiddo/src/run_pipeline.sh "$CONFIG_PATH"
