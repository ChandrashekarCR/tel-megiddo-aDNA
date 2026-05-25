
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

    stub:
    """
    # Stub: pretend we downloaded Gallus gallus
    #   - create a dummy .zip file
    #   - create a dummy base/ncbi_dataset tree that resembles real NCBI datasets

    touch ${base}.zip

    mkdir -p ${base}/ncbi_dataset/data/${params.gallus_accession}
    echo "stub_fasta_gallus_gallus" > ${base}/ncbi_dataset/data/${params.gallus_accession}/genome.fna

    # We don't need to zip the tree here; real workflow will read the base/ directory
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