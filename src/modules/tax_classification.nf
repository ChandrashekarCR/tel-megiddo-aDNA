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
    tuple val(sample_id), path("${sample_id}/kraken.tsv"), path("${sample_id}/kraken_report.tsv"), path("${sample_id}/kraken.log")

    script:
    """
    mkdir -p ${sample_id}

    kraken2 \
        --db ${params.kraken2_db} \
        --threads 12 \
        --report ${sample_id}/kraken_report.tsv \
        --output ${sample_id}/kraken.tsv \
        ${fastq} > ${sample_id}/kraken.log 2>&1
    """

    stub:
    """
    mkdir -p ${sample_id}
    printf "mock_read_id\\t0\\t100\\t1\\t0\\n" > ${sample_id}/kraken.tsv
    printf "100.00\\t100\\t100\\tno rank\\t0\\tUnclassified\\n" > ${sample_id}/kraken_report.tsv
    echo "Kraken2 stub run - mock mode" > ${sample_id}/kraken.log
    """

}

process BRACKEN {

    debug true

    tag "$sample_id-$rank"

    publishDir "${params.outdir}/06_bracken", mode: "copy"

    input:
    tuple val(sample_id), path(kraken_report), val(rank)

    output:
    tuple val(sample_id), val(rank), path("${sample_id}/${rank}.tsv"), path("${sample_id}/bracken_${rank}.log")

    script:
    """
    mkdir -p ${sample_id}

    bracken \
        -r ${params.read_len} \
        -i ${kraken_report} \
        -o ${sample_id}/${rank}.tsv \
        -d ${params.bracken_db} \
        -l ${rank[0].toUpperCase()} > ${sample_id}/bracken_${rank}.log 2>&1
    """
    
    stub:
    """
    mkdir -p ${sample_id}
    printf "name\\ttaxonomy_id\\ttaxonomy_lvl\\tkraken_assigned_reads\\tadded_reads\\tnew_est_reads\\tfraction_total_reads\\n" > ${sample_id}/${rank}.tsv
    printf "Unclassified\\t0\\tno rank\\t100\\t0\\t100\\t1.0\\n" >> ${sample_id}/${rank}.tsv
    echo "Bracken stub run for ${rank} - mock mode" > ${sample_id}/bracken_${rank}.log
    """
}