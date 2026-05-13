#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'USAGE'
Usage:
	kraken_bracken.sh --raw <raw_dir> --kraken-db <kraken_db_dir> --bracken-db <bracken_db_dir> [--out <results_dir>] [--threads <n>] [--read-length <len>] [--threshold <n>] [--continue-on-error]

Runs Kraken2 classification and Bracken abundance estimation on all single-end FASTQ/FASTQ.GZ files in the raw dataset directory.

This script is customized for inputs ending in: *.fq.gz

Options:
	--raw                Path to raw dataset directory (required)
	--out                Results directory (default: ./results)
	--kraken-db           Kraken2 database directory (required)
	--bracken-db          Bracken database directory (required)
	--threads             Kraken2 threads (default: 16)
	--read-length          Bracken read length (default: 75)
	--threshold            Bracken minimum-read threshold (passed to `bracken -t`, default: 0)
	--continue-on-error    Continue processing other samples if one fails
	-h, --help            Show help
USAGE
}

raw_dir=""
out_dir="./results"
kraken_db=""
bracken_db=""
threads=""
read_length=""
threshold="0"
continue_on_error=0

notes_file=""

RANKS=("phylum" "species")
declare -A RANK_CODE=(
	[phylum]="P"
	[class]="C"
	[order]="O"
	[family]="F"
	[genus]="G"
	[species]="S"
)

while [[ $# -gt 0 ]]; do
	case "$1" in
		--raw)
			raw_dir="$2"; shift 2 ;;
		--out)
			out_dir="$2"; shift 2 ;;
		--kraken-db)
			kraken_db="$2"; shift 2 ;;
		--bracken-db)
			bracken_db="$2"; shift 2 ;;
		--threads)
			threads="$2"; shift 2 ;;
		--read-length)
			read_length="$2"; shift 2 ;;
		--threshold)
			threshold="$2"; shift 2 ;;
		--continue-on-error)
			continue_on_error=1; shift 1 ;;
		-h|--help)
			usage; exit 0 ;;
		*)
			echo "Unknown option: $1" >&2
			usage
			exit 1
			;;
	esac
done


threads="${threads:-16}"
read_length="${read_length:-75}"

if ! [[ "$threshold" =~ ^[0-9]+$ ]]; then
	echo "Error: --threshold must be a non-negative integer, got: $threshold" >&2
	exit 1
fi

# Normalize a few paths to avoid double slashes and ugly sample ids.
raw_dir="${raw_dir%/}"
out_dir="${out_dir%/}"
kraken_db="${kraken_db%/}"
bracken_db="${bracken_db%/}"

notes_file="$out_dir/kraken_bracken_notes.tsv"

note() {
	# Columns:
	# timestamp\tsample\tinput\tstage\trank\tstatus\tmessage
	local sample="$1"
	local input="$2"
	local stage="$3"
	local rank="$4"
	local status="$5"
	local message="$6"
	printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -Is)" "$sample" "$input" "$stage" "$rank" "$status" "$message" >>"$notes_file"
}

if [[ -z "$raw_dir" ]]; then
	echo "Error: provide --raw" >&2
	usage
	exit 1
fi

if [[ -z "$kraken_db" ]]; then
	echo "Error: --kraken-db is required" >&2
	exit 1
fi

if [[ -z "$bracken_db" ]]; then
	echo "Error: --bracken-db is required" >&2
	exit 1
fi

if [[ ! -d "$raw_dir" ]]; then
	echo "Error: raw directory not found: $raw_dir" >&2
	exit 1
fi

if [[ ! -d "$kraken_db" ]]; then
	echo "Error: kraken db directory not found: $kraken_db" >&2
	exit 1
fi

if [[ ! -d "$bracken_db" ]]; then
	echo "Error: bracken db directory not found: $bracken_db" >&2
	exit 1
fi

command -v kraken2 >/dev/null 2>&1 || { echo "Error: kraken2 not found in PATH" >&2; exit 1; }
command -v bracken >/dev/null 2>&1 || { echo "Error: bracken not found in PATH" >&2; exit 1; }

# Bracken preflight: database<readlen>mers.kmer_distrib must exist.
expected_kmer_dist="$bracken_db/database${read_length}mers.kmer_distrib"
if [[ ! -f "$expected_kmer_dist" ]]; then
	echo "Error: Bracken support file missing for read length ${read_length}: $expected_kmer_dist" >&2
	echo "Hint: build Bracken files for this DB/read length (example):" >&2
	echo "  bracken-build -d \"$bracken_db\" -t $threads -l $read_length" >&2
	exit 1
fi

mkdir -p "$out_dir"

if [[ ! -f "$notes_file" ]]; then
	echo -e "timestamp\tsample\tinput\tstage\trank\tstatus\tmessage" >"$notes_file"
fi

echo "Raw dir: $raw_dir"
echo "Results dir: $out_dir"
echo "Threads: $threads"
echo "Read length: $read_length"
echo "Threshold: $threshold" # This is set to zero because there are less than 10 reads that were mapped when perfroming kraken estimation
echo "Kraken DB: $kraken_db"
echo "Bracken DB: $bracken_db"

mapfile -t files < <(
	find "$raw_dir" -type f \( \
			-name "*.fq.gz" \
		\) -print
)

if [[ ${#files[@]} -eq 0 ]]; then
	echo "Error: no FASTQ files found under: $raw_dir" >&2
	exit 1
fi

processed=0
failed=0

for fq in "${files[@]}"; do
	# Make paths comparable even if raw_dir is relative.
	raw_abs="$(realpath -m "$raw_dir")"
	fq_abs="$(realpath -m "$fq")"
	relpath="$fq_abs"
	if [[ "$fq_abs" == "$raw_abs"/* ]]; then
		relpath="${fq_abs#"$raw_abs"/}"
	fi

	# Turn relative path into a safe, unique sample id.
	sample="$relpath"
	sample="${sample//\//__}"
	sample="${sample%.fq.gz}"

	kraken_out_dir="$out_dir/kraken2/$sample"
	bracken_out_dir="$out_dir/bracken/$sample"
	mkdir -p "$kraken_out_dir" "$bracken_out_dir"

	kraken_output="$kraken_out_dir/kraken.tsv"
	kraken_report="$kraken_out_dir/kraken_report.tsv"
	kraken_log="$kraken_out_dir/kraken.log"

	echo "----"
	echo "Sample: $sample"
	echo "Input:  $fq"
	note "$sample" "$fq" "kraken2" "-" "START" "running kraken2"

	if ! kraken2 \
			--db "$kraken_db" \
			--threads "$threads" \
			--report "$kraken_report" \
			--output "$kraken_output" \
			"$fq" >"$kraken_log" 2>&1; then
		echo "Error: Kraken2 failed for sample $sample (log: $kraken_log)" >&2
		failed=$((failed + 1))
		note "$sample" "$fq" "kraken2" "-" "FAIL" "kraken2 failed (see $kraken_log)"
		if [[ "$continue_on_error" -eq 0 ]]; then
			exit 1
		fi
		continue
	fi

	if [[ ! -s "$kraken_report" ]]; then
		echo "Error: Kraken2 report empty for sample $sample: $kraken_report" >&2
		failed=$((failed + 1))
		note "$sample" "$fq" "kraken2" "-" "FAIL" "kraken2 report empty"
		if [[ "$continue_on_error" -eq 0 ]]; then
			exit 1
		fi
		continue
	fi

	# If there are no classified reads, Bracken will fail with "no reads found".
	classified_reads="$(awk '$4=="R" && $5==1 {print $2; exit}' "$kraken_report" || true)"
	classified_reads="${classified_reads:-0}"
	if [[ "$classified_reads" -eq 0 ]]; then
		echo "Note: 0 classified reads for $sample; skipping Bracken" >&2
		note "$sample" "$fq" "bracken" "-" "SKIP" "0 classified reads in kraken report"
		processed=$((processed + 1))
		continue
	fi

	for rank in "${RANKS[@]}"; do
		bracken_output="$bracken_out_dir/${rank}.tsv"
		bracken_log="$bracken_out_dir/bracken_${rank}.log"
		rank_code="${RANK_CODE[$rank]}"

		note "$sample" "$fq" "bracken" "$rank" "START" "running bracken"
		if ! bracken \
				-r "$read_length" \
				-t "$threshold" \
				-i "$kraken_report" \
				-o "$bracken_output" \
				-d "$bracken_db" \
				-l "$rank_code" >"$bracken_log" 2>&1; then
			if grep -qi "no reads found" "$bracken_log"; then
				echo "Note: Bracken reports no reads for sample $sample rank $rank; skipping" >&2
				note "$sample" "$fq" "bracken" "$rank" "SKIP" "bracken: no reads found"
				continue
			fi
			echo "Error: Bracken failed for sample $sample rank $rank (log: $bracken_log)" >&2
			failed=$((failed + 1))
			note "$sample" "$fq" "bracken" "$rank" "FAIL" "bracken failed (see $bracken_log)"
			if [[ "$continue_on_error" -eq 0 ]]; then
				exit 1
			fi
			continue
		fi

		if [[ ! -s "$bracken_output" ]]; then
			echo "Error: Bracken output empty for sample $sample rank $rank: $bracken_output" >&2
			failed=$((failed + 1))
			note "$sample" "$fq" "bracken" "$rank" "FAIL" "bracken output empty"
			if [[ "$continue_on_error" -eq 0 ]]; then
				exit 1
			fi
			continue
		fi
		note "$sample" "$fq" "bracken" "$rank" "OK" "wrote $bracken_output"
	done

	processed=$((processed + 1))
	echo "OK: finished $sample"
done

echo "----"
echo "Done. Processed: $processed, Failed: $failed"

if [[ "$failed" -gt 0 ]]; then
	exit 2
fi

# Example -:
# ./kraken_bracken.sh --raw ../data/telmgd_qced/ --out ../results/ --kraken-db ../../lu2025-12-38/Students/chandru/kraken_databases/run_gallus_standard/ --bracken-db ../../lu2025-12-38/Students/chandru/kraken_databases/run_gallus_standard/ --threads 32 --read-length 75 
