process MAKE_BLAST_DB {

    publishDir "${params.blastdb}/gallus_blast_db", mode: "copy"

    output: path("gallus_blast_db")

    script:
    """
    mkdir -p gallus_blast_db

    makeblastdb \
        -in ${params.gallus_fasta} \
        -dbtype nucl \
        -out gallus_blast_db/gallus \
        -title 
    """
}