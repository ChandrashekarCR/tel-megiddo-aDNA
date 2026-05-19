process SEQ_LEN {
    debug true

    tag "$sample_id"

    publishDir "${params.outdir}/01_seqlen", mode: "copy"

    input:
    tuple val(sample_id), path(fastq)

    output:
    tuple val(sample_id), path("${sample_id}_read_length_dist.txt")

    script:
    """
    seqkit fx2tab -l -n "$fastq" > ${sample_id}_read_length_dist.txt
    """
}

process MERGE_COUNT {
    debug true

    publishDir "${params.outdir}/01_seqlen", mode: "copy"

    input:
    path readlen_files

    output:
    path "merged_read_length_dist.txt"

    script:
    """
    cat ${readlen_files.join(' ')} > merged_read_length_dist.txt
    """
}