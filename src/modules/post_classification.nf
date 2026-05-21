process STANDARDIZE_BRACKEN {
    tag "${sample_id}-${rank}"

    publishDir "${params.outdir}/07_standardize_bracken", mode: "copy"

    input:
    tuple val(sample_id), val(rank), path(bracken_report)
    path (std_script)

    output:
    tuple val(sample_id), val(rank), path("${sample_id}/${sample_id}_${rank}.csv")

    script:
    """
    mkdir -p ${sample_id}

    python3 ${std_script} \
        --mode "standardize" \
        -i ${bracken_report} \
        -s ${sample_id} \
        -r ${rank} \
        -o ${sample_id}/${sample_id}_${rank}.csv
    """

}

process MERGE_BRACKEN {
    tag "$rank"
    publishDir "${params.outdir}/08_merged_bracken", mode: "copy"

    input:
    tuple val(rank), path(csv_files)   // all CSVs for this rank collected
    path std_script

    output:
    tuple val(rank), path("${rank}_merged.csv")

    script:
    """
    python3 ${std_script} \
        --mode merge \
        -i ${csv_files} \
        -o ${rank}_merged.csv
    """
}