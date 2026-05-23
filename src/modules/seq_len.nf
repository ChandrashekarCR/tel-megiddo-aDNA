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

    stub:
    """
    echo "read_id\t50" > ${sample_id}_read_length_dist.txt
    echo "fake_read_001\t50" >> ${sample_id}_read_length_dist.txt
    echo "fake_read_002\t50" >> ${sample_id}_read_length_dist.txt
    """

}

