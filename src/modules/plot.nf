process PLOT {

    debug true

    tag "$sample_id"

    publishDir "${params.outdir}/03_kmer_long", mode:"copy", pattern: "*.csv"
    publishDir "${params.outdir}/04_kmer_plots", mode: "copy", pattern: "*.png"


    input:
    tuple val(sample_id), path(kmer_dist)
    path plot_script

    output:
    tuple val(sample_id), path("${sample_id}_kmer_long_dist.csv"), path("${sample_id}.png")

    script:
    """
    python3 ${plot_script} -i ${kmer_dist} -o ${sample_id}_kmer_long_dist.csv -f ${sample_id}.png
    """

    stub:
    """
    echo "k,kmer_count,dkmer_dk" > ${sample_id}_kmer_long_dist.csv
    echo "20,1000,0" >> ${sample_id}_kmer_long_dist.csv
    echo "21,950,-50" >> ${sample_id}_kmer_long_dist.csv
    echo "22,900,-50" >> ${sample_id}_kmer_long_dist.csv
    touch ${sample_id}.png
    """

}