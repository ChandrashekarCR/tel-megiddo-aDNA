process SEQ_LEN {
    debug true

    tag "$sample_id"

    publishDir "${params.outdir}/01_seqlen", mode: "copy"

    input:
    tuple val(sample_id), path(fastq)

    output:
    tuple val(sample_id), path("${sample_id}_seq
}