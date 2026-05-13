#!/usr/bin/env bash
set -euo pipefail


# Default values
raw_dir=""
out_dir=""

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --raw RAW_DIR   Path to raw FASTQ directory"
    echo "  --out OUT_DIR   Output directory"
    echo "  --help          Show this help message"
    exit 1
}

# Parse arguements
while [[ $# -gt 0 ]]; do
    case $1 in 
        --raw)
            raw_dir="$2"
            shift 2
            ;;
        --out)
            out_dir="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validation checks
if [[ -z "$raw_dir" ]]; then
    echo "Error: raw_dir not specified. Use --raw or --config" >&2
    exit 1
fi

if [[ ! -d "$raw_dir" ]]; then
    echo "Error: raw_dir does not exist: $raw_dir" >&2
    exit 1
fi

# Create the output directory
if ! mkdir -p "$out_dir"; then
    echo "Error: Failed to create output directory: $out_dir" >&2
    exit 1
fi

echo "Processing FASTQ files from: $raw_dir"
echo "Output directory: $out_dir"

# Counter for processed files
processed=0
failed=0

# Create the output directory
mkdir -p $out_dir

find "$raw_dir" -type f -name "*.fq.gz" | while read -r fq; do
	base=$(basename "$fq")
	base=${base%.fq.gz}
	out_file="$out_dir/${base}.read_length_dist.tsv"

	if ! zcat "$fq" 2>/dev/null |
			awk 'NR % 4 == 2 {len=length($0); count[len]++} END {for (l in count) print l "\t" count[l]}' |
			sort -n > "$out_file"; then
        echo "Error: Failed to process $fq" >&2
        exit 1
    fi
	
    if [[ ! -s "$out_file" ]]; then
        echo "Error: Output file is empty: $out_file" >&2
        exit 1
    fi

    echo "Wrote $out_file"
done

echo "Processing complete!"
