
process DOWNLOAD_GALLUS {

    publishDir "${params.blast_db}", mode: "copy"

    input:
    val base

    output:
    path "${base}.zip"
    path "${base}"

    script:
    """
    datasets download genome accession ${params.gallus_accession} \
        --include genome \
        --filename ${base}.zip
    
    unzip ${base}.zip -d ${base}
    """

}




process MAKE_BLAST_DB {

    publishDir "${params.blast_db}/gallus_blast_db", mode: "copy"

    output: path("gallus_blast_db")

    script:
    """
    mkdir -p gallus_blast_db

    makeblastdb \
        -in ${params.gallus_fasta} \
        -dbtype nucl \
        -out gallus_blast_db/gallus \
        -title "Gallus_gallue_GRCg7b" \
        -parse_seqids \
        -taxid 9031
    """
}