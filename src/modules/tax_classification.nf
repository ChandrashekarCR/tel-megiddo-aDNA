// Classification
//  Kraken2 Taxonomic Classificaiton
//  Bracken abundance estimation

process KRAKEN {

    debug true

    tag "$sample_id"

    publishDir "${params.outdir}/05_kraken", mode: "copy"

    input:
    tuple val(sample_id), path(fastq)

    output:
    tuple val(sample_id), path("${sample_id}/kraken.tsv"), path("${sample_id}/kraken_report.tsv")

    script:
    """
    mkdir -p ${sample_id}

    kraken2 \
        --db ${params.kraken2_db} \
        --threads ${task.cpus} \
        --report ${sample_id}/kraken_report.tsv \
        --output ${sample_id}/kraken.tsv \
        ${fastq}
    """

}

process BRACKEN {

    debug true

    tag "$sample_id-$rank"

    publishDir "${params.outdir}/06_bracken", mode: "copy"

    input:
    tuple val(sample_id), path(kraken_report)
    val rank

    output:
    tuple val(sample_id), val(rank), path("${sample_id}_${rank}.tsv")

    script:
    def rank_short = rank.take(1).toUpperCase()

    """
    bracken \
        -r ${params.read_len} \
        -i ${kraken_report} \
        -o ${sample_id}_${rank}.tsv \
        -d ${params.bracken_db} \
        -l ${rank_short}
    """
}