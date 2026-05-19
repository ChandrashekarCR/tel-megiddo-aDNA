process KMER {

    debug true

    tag "$sample_id"

    publishDir "${params.outdir}/02_kmer", mode:"copy"

    input:
    tuple val(sample_id), path(read_len)
    path kmer_script

    output:
    tuple val(sample_id), path("${sample_id}_kmer_dist.csv")

    script:
    """
    python3 ${kmer_script} -i ${read_len} -o ${sample_id}_kmer_dist.csv
    """

}